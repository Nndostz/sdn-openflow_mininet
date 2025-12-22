from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, icmp

class FinalSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # ❌ TIDAK PASANG FLOW APA PUN
        # Semua paket akan masuk ke controller
        pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)

        if not ip:
            return

        # 1️⃣ DROP ICMP dari h1
        if ip.src == '10.0.0.1' and pkt.get_protocol(icmp.icmp):
            return  # DROP → DIJAMIN

        # 2️⃣ FORWARD TCP h2 → h3
        if ip.src == '10.0.0.2' and ip.dst == '10.0.0.3' and pkt.get_protocol(tcp.tcp):
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        # 3️⃣ MODIFY HEADER h4
        elif ip.src == '10.0.0.4':
            actions = [
                parser.OFPActionSetField(eth_src='00:11:22:33:44:99'),
                parser.OFPActionOutput(ofproto.OFPP_NORMAL)
            ]
        else:
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=msg.match['in_port'],
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(out)
