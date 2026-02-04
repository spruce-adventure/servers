{ config, ... }:
let
  inherit (config.constants) tunnelPort wgPort;
  proxyInnerPort = 8080;
  proxyDomain = "cdn-1.pang8578sprung.xyz";
in
{
  sops.secrets.shadowsocksPassword = {
    owner = "root";
    mode = "0400";
    restartUnits = [ "shadowsocks-node-gateway.service" ];
  };
  sops.secrets.proxyAuthConfig = {
    owner = "root";
    mode = "0400";
    format = "yaml";
    restartUnits = [ "shadowsocks-node-gateway.service" ];
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
    streamConfig = ''
      server {
        listen 443 ssl;
        proxy_pass 127.0.0.1:${toString proxyInnerPort};

        ssl_certificate /var/lib/acme/${proxyDomain}/fullchain.pem;
        ssl_certificate_key /var/lib/acme/${proxyDomain}/key.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
      }
    '';
  };
  security.acme = {
    acceptTerms = true;
    defaults.email = "il5y115me@mozmail.com";
    certs.${proxyDomain} = {
      webroot = "/var/lib/acme/acme-challenge";
      group = "nginx";
    };
  };
  networking.firewall.allowedUDPPorts = [ tunnelPort ];
  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
