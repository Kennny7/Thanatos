#!/usr/bin/env bash
# Thanatos Linux/macOS/Termux PATH Installer
# Run: chmod +x install_cli.sh && ./install_cli.sh

THANATOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$THANATOS_DIR/thanatos"

echo "[•] Thanatos Directory: $THANATOS_DIR"

SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.profile"
fi

EXPORT_LINE="export PATH=\"\$PATH:$THANATOS_DIR\""

if grep -Fxq "$EXPORT_LINE" "$SHELL_RC" 2>/dev/null; then
    echo "[✓] Thanatos already exists in $SHELL_RC"
else
    echo "" >> "$SHELL_RC"
    echo "# Thanatos AI CLI" >> "$SHELL_RC"
    echo "$EXPORT_LINE" >> "$SHELL_RC"
    echo "[✓] Appended Thanatos to $SHELL_RC"
fi

echo "Restart your terminal or run: source $SHELL_RC"
echo "You can now execute 'thanatos' from any folder!"
