import asyncio
from pathlib import Path

import aiofiles
from jinja2 import Template
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from deploy_bot.auth import auth
from deploy_bot.config import config
from deploy_bot.exception import do_default_reply_on_any_error


templates = Path(__file__).parents[1] / "templates"


async def shell(cmd: str) -> tuple[int, str | None, str | None]:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout: bytes
    stderr: bytes

    stdout, stderr = await proc.communicate()

    return proc.returncode, stdout.decode() or None, stderr.decode() or None


async def create_or_update_poetry_environment(component_name: str):
    await shell(
        cmd=(
            f"cd {config.bot_components_code_path}/{component_name} "
            "&& poetry install"
        )
    )


async def get_path_to_python_executor() -> str:
    code, out, err = await shell("poetry env info")

    if code != 0:
        raise Exception(f"Команда poetry env info упала с ошибкой: {err}")

    for info_line in out.split("\n"):
        if info_line.lower().startswith("executable"):
            return info_line.replace(" ", "").replace("Executable:", "").strip()

    raise Exception("Непредвиденный вывод команды poetry env info")


async def get_secrets(component_name: str) -> list[str]:
    async with aiofiles.open(f"{config.bot_secrets_path}/{component_name}/.env") as secrets:
        return [f"'{secret.strip()}'" for secret in await secrets.readlines()]


async def git_clone_with_replace(component_name: str, tag: str):
    code_path = f"{config.bot_components_code_path}/{component_name}"
    compound_command = (
        f"rm -rf {code_path}"
        f"&& git clone -b main {tag} https://github.com/meehighlov/{component_name} {code_path}"
    )

    await shell(compound_command)


@auth
@do_default_reply_on_any_error
async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    component_name, tag = context.args
    component_name_slug = component_name.replace("-", "_")

    await update.message.reply_text(f"Клонирую репозиторий для {component_name}")

    await git_clone_with_replace(component_name=component_name, tag=tag)

    await update.message.reply_text(f"Обновляю виртуальное окружение для {component_name}")

    await create_or_update_poetry_environment(component_name=component_name)

    await update.message.reply_text(f"Ищу интерпретатор для {component_name}")
    executor_path = await get_path_to_python_executor()

    await update.message.reply_text(f"Собираю unit-файл для {component_name}")

    async with aiofiles.open(templates / "unit.service", mode="r") as template_file:
        template_text = await template_file.read()
        template = Template(template_text)

    secrets = await get_secrets(component_name=component_name)

    data = dict(
        description=f"unit file for {component_name}",
        env_vars=secrets,
        exec_start=f"{executor_path} {config.bot_components_code_path}/{component_name_slug}"
    )

    unit_file: str = template.render(data)

    await update.message.reply_text(f"Обновляю существующий unit-file для {component_name}")

    async with aiofiles.open(f"{config.bot_unit_files_path}/{component_name}.service", mode="w") as service_file:
        await service_file.write(unit_file)

    await update.message.reply_text(f"Компонент {component_name} готов к запуску")


async def rollout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    component_name = context.args[0]

    await update.message.reply_text("Запускаю systemctl daemon-reload")
    await shell(f"systemctl daemon-reload")

    await update.message.reply_text(f"Запускаю сервис {component_name}")
    _, out, _ = await shell(
        f"cd .. "
        f"&& service {component_name} start "
        f"|| service {component_name} status"
    )

    await update.message.reply_text(out)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Готов катить")


app = ApplicationBuilder().token(config.bot_token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("deploy", deploy))
app.add_handler(CommandHandler("rollout", rollout))

app.run_polling()
