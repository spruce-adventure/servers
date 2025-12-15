{
  writeShellApplication,
  nixos-rebuild,
}:
writeShellApplication {
  name = "rebuild-server";
  runtimeInputs = [
    nixos-rebuild
  ];
  text = ''
    name=$1
    address="$(cat "modules/by-name/constants/$name.txt")"

    if git diff-tree --no-commit-id --name-only -r HEAD | grep -q '^flake\.lock$'; then
      flake_lock_changed=true
      command="boot"
      echo "flake.lock changed in the last commit. Performing '$command' and reboot."
    else
      flake_lock_changed=false
      command="switch"
      echo "flake.lock did not change. Performing '$command'."
    fi

    nixos-rebuild "$command" \
      --flake . \
      --use-remote-sudo \
      --use-substitutes \
      --target-host "github-actions@$address" \
      --build-host builder@liferooter.dev \
      --log-format bar-with-logs

    if [ "$flake_lock_changed" = true ]; then
      echo "Rebooting $name..."
      ssh "github-actions@$address" sudo systemctl reboot
    fi
  '';
}
