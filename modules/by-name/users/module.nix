{ pkgs, ... }:
{
  programs.fish.enable = true;

  security.sudo.wheelNeedsPassword = false;
  services.getty.autologinUser = "root";

  users.users = {
    alexkarachun = {
      isNormalUser = true;
      extraGroups = [ "wheel" ];
      shell = pkgs.fish;
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOeoKxT/YbOkRXysyT3NUWAs0KMwyxUC8ZjyxD/ml5L2 alex@karachun.com"
      ];
    };
    liferooter = {
      isNormalUser = true;
      extraGroups = [ "wheel" ];
      shell = pkgs.fish;
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPqqape1/IJC8PK+7lJxwM9N9Oo4SK7HZ7SnCMZjmaTR liferooter@computer"
      ];
    };

    github-actions = {
      isNormalUser = true;
      extraGroups = [ "wheel" ];
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIONinDFkfwNXOVh9x6kq4NBYFPWhLOO35fY0KvzlFATp actions@github.com"
      ];
    };
  };
}
