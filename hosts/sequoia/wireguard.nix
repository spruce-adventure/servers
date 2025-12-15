{
  lib,
  config,
  pkgs,
  self,
  ...
}:
let
  inherit (lib) getExe getExe';
  inherit (config.constants) wgPort subnetPrefix;

  iptables = "${pkgs.iptables}/bin/iptables";
  wg = getExe' pkgs.wireguard-tools "wg";

  addPeersScript = pkgs.writeScriptBin "add-peers.nu" ''
    #! ${getExe pkgs.nushell}

    def main [] {
      let peers = open ${config.sops.secrets.wireguardPeerKeys.path}
        | from yaml
        | transpose name key
        | enumerate
        | flatten
        | insert pubkey {|peer| $peer.key | ${wg} pubkey}
        | insert allowed_ips {|peer| $"${subnetPrefix}.($peer.index + 2)/32"}

      let server_key = open --raw ${config.sops.secrets.wireguardKey.path}

      let config = $peers
        | each {|peer|
          $"[Peer]\n# friendly_name = ($peer.name)\nPublicKey = ($peer.pubkey)\nAllowedIPs = ($peer.allowed_ips)\n"
        }
        | str join "\n"
        | $"[Interface]\nListenPort = ${toString wgPort}\nPrivateKey = ($server_key)\n\n" + $in

      let config_path = "/run/wireguard.conf"
      touch $config_path
      chmod 600 $config_path
      chown wireguard-exporter:wireguard-exporter $config_path
      $config | save -f $config_path

      $peers
      | each {|peer|
        ${wg} set wg0 peer $peer.pubkey allowed-ips $peer.allowed_ips
      }
    }
  '';
in
{
  networking.nat.enable = true;

  networking.firewall.allowedUDPPorts = [ wgPort ];
  networking.firewall.allowedTCPPorts = [ wgPort ];

  sops.secrets.wireguardKey = {
    sopsFile = ./wireguard-server.yml;

    owner = "root";
    mode = "0400";
    restartUnits = [
      "wg-quick-wg0.service"
      "prometheus-wireguard-exporter.service"
    ];
  };

  sops.secrets.wireguardPeerKeys = {
    sopsFile = "${self}/wireguard-clients.yml";
    key = "";
    format = "yaml";

    owner = "root";
    mode = "0400";
    restartUnits = [
      "wg-quick-wg0.service"
      "prometheus-wireguard-exporter.service"
    ];
  };

  networking.wg-quick.interfaces = {
    wg0 = {
      address = [
        "${subnetPrefix}.1/24"
      ];
      autostart = true;
      listenPort = wgPort;

      privateKeyFile = config.sops.secrets.wireguardKey.path;

      postUp = ''
        ${iptables} -A FORWARD -i %i -j ACCEPT
        ${iptables} -A FORWARD -o %i -j ACCEPT
        ${iptables} -t mangle -A FORWARD -o %i -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmt
        ${iptables} -t nat -A POSTROUTING -o ens3 -j MASQUERADE
        ${getExe addPeersScript}
      '';
      postDown = ''
        ${iptables} -D FORWARD -i %i -j ACCEPT
        ${iptables} -D FORWARD -o %i -j ACCEPT
        ${iptables} -t mangle -D FORWARD -o %i -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmt
        ${iptables} -t nat -D POSTROUTING -o ens3 -j MASQUERADE
      '';
    };
  };
}
