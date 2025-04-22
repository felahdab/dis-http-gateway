import os
from dotenv import load_dotenv
import ipaddress

load_dotenv()


def is_multicast_address(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_multicast
    except ValueError:
        return False

def load_config_from_env():
    # Tokens
    default_token = os.getenv("HTTP_BEARER_TOKEN", "")

    # Receiver Configuration
    udp_receiver_ip = os.getenv("DIS_RECEIVER_IP", "0.0.0.0")
    udp_receiver_port = int(os.getenv("DIS_RECEIVER_PORT", "3000"))
    udp_receiver_mode = int(os.getenv("DIS_RECEIVER_MODE", 1))  # 0 = unicast | 1 = multicast | 2 = broadcast
    if (udp_receiver_mode == 1):
        if not is_multicast_address(udp_receiver_ip):
            raise ValueError(f"Invalid multicast IP address for receiver: '{udp_receiver_ip}'. Expected an address in the range 224.0.0.0 to 239.255.255.255.")

    http_endpoint_receiver = os.getenv("HTTP_ENDPOINT_RECEIVER", "http://example.com/api/receive")
    http_token_receiver = os.getenv("HTTP_BEARER_TOKEN_RECEIVER", default_token)
    
    remote_dis_site = int(os.getenv("REMOTE_DIS_SITE", 1))
    remote_dis_application = int(os.getenv("REMOTE_DIS_APPLICATION", 42))

    # Emitter Configuration
    udp_emitter_ip = os.getenv("DIS_EMITTER_IP", "127.0.0.255")
    udp_emitter_port = int(os.getenv("DIS_EMITTER_PORT", "4000"))
    udp_emitter_mode = int(os.getenv("DIS_EMITTER_MODE", 2))  # 0 = unicast | 1 = multicast | 2 = broadcast
    if (udp_emitter_mode == 1):
        if not is_multicast_address(udp_emitter_ip):
            raise ValueError(f"Invalid multicast IP address for emitter: '{udp_emitter_ip}'. Expected an address in the range 224.0.0.0 to 239.255.255.255.")
        
    http_endpoint_poller = os.getenv("HTTP_ENDPOINT_POLLER", "http://example.com/api/poll")
    http_ack_endpoint = os.getenv('HTTP_ACK_ENDPOINT', "http://example.com/api/ack")
    poll_interval = float(os.getenv("POLL_INTERVAL", "5"))
    http_token_poller = os.getenv("HTTP_BEARER_TOKEN_POLLER", default_token)
    
    # Debug mode. If true, use dummy data, else poll engagements from API
    is_debug_on = os.getenv("IS_DEBUG_ON", "false") == "true"

    return {
        "remote_dis_site" : remote_dis_site,
        "remote_dis_application" : remote_dis_application,
        "receiver": {"ip": udp_receiver_ip, "port": udp_receiver_port, "mode": udp_receiver_mode},
        "emitter": {"ip": udp_emitter_ip, "port": udp_emitter_port, "mode": udp_emitter_mode},
        "http_receiver": http_endpoint_receiver,
        "http_token_receiver": http_token_receiver,
        "http_poller": http_endpoint_poller,
        "http_ack_endpoint" : http_ack_endpoint,
        "http_token_poller": http_token_poller,
        "poll_interval": poll_interval,
        "is_debug_on": is_debug_on,
    }
