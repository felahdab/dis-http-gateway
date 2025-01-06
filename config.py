import os

def load_config_from_env():
    own_dis_site = os.getenv("OWN_DIS_SITE", 29)
    own_dis_application = os.getenv("OWN_DIS_APPLICATION", 1)

    remote_dis_site = os.getenv("REMOTE_DIS_SITE", 1)
    remote_dis_application = os.getenv("REMOTE_DIS_APPLICATION", 42)

    # Receiver Configuration
    udp_receiver_ip = os.getenv("DIS_RECEIVER_IP", "0.0.0.0")
    udp_receiver_port = int(os.getenv("DIS_RECEIVER_PORT", "3000"))
    udp_receiver_mode = os.getenv("DIS_RECEIVER_MODE", "multicast")

    # Emitter Configuration
    udp_emitter_ip = os.getenv("DIS_EMITTER_IP", "127.0.0.255")
    udp_emitter_port = int(os.getenv("DIS_EMITTER_PORT", "4000"))
    udp_emitter_mode = os.getenv("DIS_EMITTER_MODE", "broadcast")

    # API Configuration
    http_endpoint_receiver = os.getenv("HTTP_ENDPOINT_RECEIVER", "http://example.com/api/receive")
    http_endpoint_poller = os.getenv("HTTP_ENDPOINT_POLLER", "http://example.com/api/poll")
    poll_interval = float(os.getenv("POLL_INTERVAL", "5"))

    # Tokens
    default_token = os.getenv("HTTP_BEARER_TOKEN", "")
    http_token_receiver = os.getenv("HTTP_BEARER_TOKEN_RECEIVER", default_token)
    http_token_poller = os.getenv("HTTP_BEARER_TOKEN_POLLER", default_token)

    return {
        "own_dis_site" : own_dis_site,
        "own_dis_application" : own_dis_application,
        "remote_dis_site" : remote_dis_site,
        "remote_dis_application" : remote_dis_application,
        "receiver": {"ip": udp_receiver_ip, "port": udp_receiver_port, "mode": udp_receiver_mode},
        "emitter": {"ip": udp_emitter_ip, "port": udp_emitter_port, "mode": udp_emitter_mode},
        "http_receiver": http_endpoint_receiver,
        "http_token_receiver": http_token_receiver,
        "http_poller": http_endpoint_poller,
        "http_token_poller": http_token_poller,
        "poll_interval": poll_interval,
    }
