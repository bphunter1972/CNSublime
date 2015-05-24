"""
Commands for working with Cavium logfiles.
"""

import sublime
import sublime_plugin
import re


__author__ = 'Brian Hunter'
__email__ = 'brian.hunter@cavium.com'

# Regular expressions to find common line elements
Error_rexp = r'^(%[EFW]-)|(\*{3} %[EWF]-|(Error-))'
Debug_rexp = r'^%[IDEFW]-.*\{'
Time_rexp = re.compile(r'.*\{\s+(\d+)\.(\d+)\}')
FileName_rexp = re.compile(r'^%[IDEFW]-\(\s*(.*):\s*(\d+)')


class CnBaseCommand(sublime_plugin.TextCommand):
    all_dbg_pts = []
    all_times_pts = []
    middles = None

    def run(self, edit):
        """
        For debug purposes only
        """
        # times = self.get_times()
        # for t in times:
        #     print t[0], t[1]
        pass

    def get_dbg(self):
        if len(self.all_dbg_pts):
            return self.all_dbg_pts
        else:
            sublime.status_message("Examining logfile...")
            self.all_dbg_pts = self.view.find_all(Debug_rexp)
            self.all_dbg_pts = [it.a for it in self.all_dbg_pts]
            sublime.status_message("")
            return self.all_dbg_pts

    # def get_times(self):
    #     if self.all_times_pts:
    #         return self.all_times_pts
    #     else:
    #         dbg = self.get_dbg()
    #         lines = [self.view.substr(self.view.line(it)) for it in dbg]
    #         rexp_res = [Time_rexp.match(it) for it in lines]
    #         times = [int(it.group(1)) for it in rexp_res if it]
    #         self.all_times_pts = zip(times, dbg)
    #         return self.all_times_pts

    def goto_pt(self, pt):
        self.view.sel().clear()
        reg = sublime.Region(pt, pt)
        self.view.sel().add(reg)
        self.view.show_at_center(pt)

    def getMiddle(self):
        if self.middles is None:
            sublime.status_message("Examining logfile...")
            regions = self.get_dbg()
            lines = [self.view.substr(self.view.line(it)) for it in regions]
            middles = [it.find('{') for it in lines]
            zips = zip(regions, middles)
            self.middles = [sublime.Region(it[0] + 3, it[0] + it[1]) for it in zips]
            sublime.status_message("")
        return self.middles


class ToggleMiddleCommand(CnBaseCommand):

    """
    Hides the fields for file name, line number, and hierarchy.
    Or, un-hides them.
    """

    def run(self, edit):
        regions = self.getMiddle()
        if not regions:
            return
        folding = not self.view.fold(regions[0])
        func = self.view.unfold if folding else self.view.fold
        func(regions)


class FindNextErrorCommand(CnBaseCommand):

    """
    Jumps to the next error line, wrapping if necessary
    """

    def run(self, edit):
        # add 3 so user can search repeatedly
        pt = self.view.sel()[0].a + 3
        new_region = self.view.find(Error_rexp, pt)
        if new_region:
            self.goto_pt(new_region.a)
        else:
            sublime.status_message("Search wrapped")
            new_region = self.view.find(Error_rexp, 0)
            if new_region:
                self.goto_pt(new_region.a)
            else:
                sublime.status_message("No errors found.")


class FindPrevErrorCommand(CnBaseCommand):

    """
    Jumps to the Prev error line, wrapping if necessary
    """

    def run(self, edit):
        regions = self.view.find_all(Error_rexp)
        if not regions:
            sublime.status_message("No errors found.")
        else:
            # Get the region that occurs previous to this one
            curr_pt = self.view.sel()[0].a
            try:
                region = [it for it in regions if it.a < curr_pt][-1]
            except IndexError:
                region = regions[-1]
                sublime.status_message("Search wrapped")

            self.goto_pt(region.a)


# class PromptGotoTimeCommand(sublime_plugin.WindowCommand):

#     """
#     Stolen directly from goto_line.
#     """

#     def run(self):
#         self.window.show_input_panel("Go To Time (ns):", "", self.on_done, None, None)
#         pass

#     def on_done(self, text):
#         try:
#             line = int(text)
#             if self.window.active_view():
#                 self.window.active_view().run_command("goto_time", {"time": line})
#         except ValueError:
#             pass


# class GotoTimeCommand(CnBaseCommand):

#     def run(self, edit, time):
#         times = self.get_times()
#         for t in times:
#             if t[0] >= time:
#                 self.goto_pt(t[1])
#                 return
#         sublime.status_message("logfile does not go that high")


# class GotoFileCommand(sublime_plugin.WindowCommand):

#     def run(self):
#         curr_view = self.window.active_view()
#         pt = curr_view.sel()[0]
#         region = curr_view.line(pt)
#         line = curr_view.substr(region)
#         match = FileName_rexp.match(line)
#         if match:
#             file_name, line_num = match.groups()
#             fname = "%s:%d" % (file_name, int(line_num))
#             print(fname)
#             # self.window.open_file(fname, sublime.ENCODED_POSITION)
#             self.window.run_command('goto_anything', fname)
#         else:
#             sublime.error_message("Line has no associated file")

"""
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.fifo.rxb_fifo.gen_bnk1[1].fifo_mem_bnk1
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.gen_mix[0].mix.mix_bnk
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.gen_mix[1].mix.mix_bnk
%W-(..............................:...0)[env.ingress_sb.cmp.........................................................]{..35044.132} TLP:000001 TAG:09 TLP:   MEM_REQ FMT: WITH_DATA_4_DWORD ADDR:062b98cea4330c4c BE1:f BE2:f DATA:[ 41 97 f6 20] differs from SWI:000038 TAG:00 TLP:   MEM_REQ FMT: WITH_DATA_3_DWORD ADDR:0000000000000c40 BE1:0 BE2:0 DATA:[ 41 97 f6 20 83 61 56 54 58 d2 1a b7 d9 e2 62 3c c6 15 e7 64 ea 7c b4 22 ec...]
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.infifo.infifo_gmp
%I-(                    CNLogfile.py: 148)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.infifo.infifo_smu
%F-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.rxb.x2p.skid_bnk
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.txb.fifo.bulk_fifo.fifo_mem_bnk0
%I-(                    mem_env.sv: 241)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.txb.fifo.bulk_fifo.fifo_mem_bnk1
%W-(                    logfile: 33)[cmr_env.mem_env                                                            ]{      0.000} Found memory bgx_cmr_tb_top.dut_cmr.txb.gen_mix[0].mix.mix_bnk
%I-(          x2p_p2m_grant_drv.sv: 173)[cmr_env.x2p_env.p2m_agent.grant_drv                                        ]{  13997.990} Sending grant for BGX1 in 32 cycles.
%I-(                    bcs_mon.sv: 601)[cmr_env.bcs_smu_env.mon                                                    ]{  13997.990} RX: LMAC:1 PID:000323 LMAC:1 [ 15 fe dd 47 59 cb 45 26] cnt:   96 
%I-(           cmr_fill_counter.sv: 155)[cmr_env.rx_fill_counter                                                    ]{  13997.990} RX: LMAC:1 num_entries +  1   = 862
%I-(             bcs_cmr_rx_drv.sv: 131)[cmr_env.bcs_smu_env.cmr_rx_agent.drv                                       ]{  13997.990} RX: PID:000325 LMAC:3 [ bf 30 4e 72 fa 6d 61 5f] cnt:   80 
%I-(                    bcs_mon.sv: 601)[cmr_env.bcs_smu_env.mon                                                    ]{  13998.545} RX: LMAC:3 PID:000325 LMAC:3 [ bf 30 4e 72 fa 6d 61 5f] cnt:   80 
%I-(           cmr_fill_counter.sv: 155)[cmr_env.rx_fill_counter                                                    ]{  13998.545} RX: LMAC:3 num_entries +  1   = 616
%I-(                credits_cnt.sv: 388)[cmr_env.x2p_env.x2p_credits_BGX1                                           ]{  13999.100} 1 credit(s) returned to x2p_credits_BGX1. Total available credits: 1
%E-(                x2p_m2p_mon.sv: 223)[cmr_env.x2p_env.m2p_agent.m2p_mon                                          ]{  14001.875} MON: X2P Trans <no_x2p_uid>:000114 SOP:0 EOP:0 DATA:0x7dca1530d074b47a95bb93ac0e5670fc PNUM:0x930 PKND:0x22 REASM:0x01 BVAL:0x0 ERR:0x0
%I-(           cmr_fill_counter.sv: 175)[cmr_env.rx_fill_counter                                                    ]{  14001.875} RX: LMAC:3 num_entries -  1   = 615
%I-(             bcs_cmr_rx_drv.sv: 131)[cmr_env.bcs_smu_env.cmr_rx_agent.drv                                       ]{  14002.985} RX: PID:000323 LMAC:1 [ c8 93 8b 7a 12 16 80 36] cnt:  104  FILTER
%I-(                    bcs_mon.sv: 601)[cmr_env.bcs_smu_env.mon                                                    ]{  14003.540} RX: LMAC:1 PID:000323 LMAC:1 [ c8 93 8b 7a 12 16 80 36] cnt:  104  FILTER
%I-(           cmr_fill_counter.sv: 158)[cmr_env.rx_fill_counter                                                    ]{  14003.540} RX: LMAC:1 num_entries +(1/2) = 862
%I-(             bcs_cmr_rx_drv.sv: 131)[cmr_env.bcs_smu_env.cmr_rx_agent.drv                                       ]{  14003.540} RX: PID:000325 LMAC:3 [ e7 e9 11 f7 ef 3b 1c 4a] cnt:   88 
%W-(..............................:...0)[env.ingress_sb.cmp.........................................................]{..35044.132} TLP:000001 TAG:09 TLP:   MEM_REQ FMT: WITH_DATA_4_DWORD ADDR:062b98cea4330c4c BE1:f BE2:f DATA:[ 41 97 f6 20] differs from SWI:000038 TAG:00 TLP:   MEM_REQ FMT: WITH_DATA_3_DWORD ADDR:0000000000000c40 BE1:0 BE2:0 DATA:[ 41 97 f6 20 83 61 56 54 58 d2 1a b7 d9 e2 62 3c c6 15 e7 64 ea 7c b4 22 ec...]
%I-(                credits_cnt.sv: 451)[cmr_env.x2p_env.x2p_credits_BGX1                                           ]{  14004.095} 1 credit(s) decremented from x2p_credits_BGX1. Total available credits: 0
%I-(                    bcs_mon.sv: 601)[cmr_env.bcs_smu_env.mon                                                    ]{  14004.095} RX: LMAC:3 PID:000325 LMAC:3 [ e7 e9 11 f7 ef 3b 1c 4a] cnt:   88 
%I-(           cmr_fill_counter.sv: 158)[cmr_env.rx_fill_counter                                                    ]{  14004.095} RX: LMAC:3 num_entries +(1/2) = 615
%I-(             bcs_cmr_rx_drv.sv: 131)[cmr_env.bcs_smu_env.cmr_rx_agent.drv                                       ]{  14004.095} RX: PID:000324 LMAC:2 [ 07 b3 5d 39 53 b1 b2 52] cnt:   72 
%I-(                    bcs_mon.sv: 601)[cmr_env.bcs_smu_env.mon                                                    ]{  14004.650} RX: LMAC:2 PID:000324 LMAC:2 [ 07 b3 5d 39 53 b1 b2 52] cnt:   72 
%I-(           cmr_fill_counter.sv: 158)[cmr_env.rx_fill_counter                                                    ]{  14004.650} RX: LMAC:2 num_entries +(1/2) = 892
%I-(             bcs_cmr_rx_drv.sv: 131)[cmr_env.bcs_smu_env.cmr_rx_agent.drv                                       ]{  14007.980} RX: PID:000323 LMAC:1 [ e6 f6 8f 81 05 ce a7 58] cnt:  112 
%I-(            pktgen_base_hdr.sv: 122)[skip_hdr                                                                   ]{  15835.040} Packed header pktgen_pkg::skip_hdr_c. _packer.size now = 47: [[ ]]
%I-(            pktgen_base_hdr.sv: 122)[eth_hdr                                                                    ]{  15835.040} Packed header bgxc_pkg::pktgen_eth_hdr_c. _packer.size now = 59: [
[12 bytes]
.000   84 3b 94 5b cc 8c db 79
.008   ce 7b a2 1d
]
%I-(            pktgen_base_hdr.sv: 122)[etype_hdr[0]                                                               ]{  15835.040} Packed header pktgen_pkg::etype_hdr_c. _packer.size now = 61: [[ e2 5d ]]
%I-(            pktgen_base_hdr.sv: 122)[payload_hdr                                                                ]{  15835.040} Packed header pktgen_pkg::payload_c. _packer.size now = 459: [
%I-(                 pktgen_pkt.sv: 618)[pkt                                                                        ]{  15925.505} hdr_q now = pktgen_pkg::skip_hdr_c -> pktgen_pkg::eth_hdr_c -> pktgen_pkg::etype_hdr_c -> pktgen_pkg::payload_c -> pktgen_pkg::term_hdr_c
%I-(              cmr_rx_pkt_sb.sv: 239)[cmr_env.rx_pkt_sb                                                          ]{  15925.505} RX: LMAC:2 Looking at 1 PID:000015 - [ 39 bytes]  44 1f 96 cc 1c 24 ec 2a...
"project/verif/vkits/cmr/cmr_rx_pkt_sb.sv", 301: cmr_pkg::\rx_pkt_sb_c::check_unpred_pkt .unnamed$$_5.unnamed$$_6.unnamed$$_17: started at 15925505000fs failed at 15925505000fs
    Offending 'exp_p.pkt_cfg.cmn_cfg'
%F-(**************cmr_rx_pkt_sb.sv:*301)[cmr_env.rx_pkt_sb**********************************************************]{**15925.505} Eek!
*************************************************************************
Testbench Stats
      Sim host: cahw8
%I-
"""
