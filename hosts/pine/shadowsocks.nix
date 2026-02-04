{ config, ... }:
let
  inherit (config.constants) tunnelPort wgPort;
  proxyInnerPort = 80;
in
{
  sops.secrets.shadowsocksPassword = {
    owner = "root";
    mode = "0400";
    restartUnits = [ "shadowsocks-local.service" ];
  };
  sops.secrets.proxyAuthConfig = {
    owner = "root";
    mode = "0400";
    format = "yaml";
    restartUnits = [ "shadowsocks-local.service" ];
  };
  services.shadowsocks-nodes.gateway = {
    role = "local";
    passwordFile = config.sops.secrets.shadowsocksPassword.path;
    config = {
      server = config.constants.serverAddress;
      server_port = tunnelPort;

      method = "chacha20-ietf-poly1305";

      locals = [
        {
          protocol = "tunnel";

          forward_address = "127.0.0.1";
          forward_port = wgPort;

          local_address = "0.0.0.0";
          local_port = tunnelPort;

          fast_open = true;

          mode = "udp_only";
        }
        {
          protocol = "http";

          local_address = "127.0.0.1";
          local_port = proxyInnerPort;

          http_auth_config_path = config.sops.secrets.proxyAuthConfig.path;
        }
      ];
    };
  };
  services.nginx = {
    enable = true;
    virtualHosts."cdn-1.pang8578sprung.xyz" = {
      forceSSL = true;
      enableACME = true;
      locations."/" = {
        proxyPass = "http://127.0.0.1:${toString proxyInnerPort}";
      };
    };
  };
  security.acme = {
    acceptTerms = true;
    defaults.email = "il5y115me@mozmail.com";
  };
  networking.firewall.allowedUDPPorts = [ tunnelPort 443 ];
}
