#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${UKRCODE_REPOSITORY:-https://github.com/UkrCodeOfficial/UkrCode.git}"
INSTALL_DIR="${UKRCODE_HOME:-$HOME/.ukrcode}"

for command in git python3; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Помилка: потрібна команда $command" >&2
        exit 1
    fi
done

echo "Завантаження UkrCode у $INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
    git -C "$INSTALL_DIR" pull --ff-only
else
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPOSITORY" "$INSTALL_DIR"
fi

python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/python" -m pip install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -e "$INSTALL_DIR"

mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/.venv/bin/ucod" "$HOME/.local/bin/ucod"
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
fi

if command -v npm >/dev/null 2>&1 && command -v code >/dev/null 2>&1; then
    (cd "$INSTALL_DIR/vscode-extension" && npm install --no-fund --no-audit)
    (cd "$INSTALL_DIR/vscode-extension" && npm run package)

    shopt -s nullglob
    extension_files=("$INSTALL_DIR"/vscode-extension/*.vsix)
    shopt -u nullglob

    if [[ ${#extension_files[@]} -gt 0 ]]; then
        code --install-extension "${extension_files[0]}" --force
    else
        echo "Попередження: VSIX не знайдено у $INSTALL_DIR/vscode-extension" >&2
    fi
fi

echo "UkrCode встановлено у $INSTALL_DIR"
echo "У поточному терміналі виконайте: export PATH=\"$HOME/.local/bin:\$PATH\""
echo "Потім перевірте: ucod --version"
echo "Токен Telegram зберігайте у $INSTALL_DIR/.env, а потім запускайте: ucod run examples/telegram-bot.ucod"