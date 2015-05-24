import sublime, sublime_plugin
import re
# from collections import defaultdict, namedtuple

# CSR_FILE = r"/nfs/cadv2/aaviananda/intr/t88/rtl/nic/nic.csr.txt"

# enhance? class
registers = {}

def parse_csr_file(fname):
   # print("Parsing file " + fname)
   flines = ''
   with open(fname, "r") as f:
      flines = str(f.read())
   parse_csr(flines)

def parse_csr(flines):
   # register = namedtuple('register', 'name, lname, desc')
   reg = re.compile(r"(?P<longname>(^\$\S+))(?P<desc>(.*?)(?=^$))", re.DOTALL | re.MULTILINE)
   for match in reg.finditer(flines):
      # name = re.sub(r"[^\w]|\d", "", match.group('longname'))
      # name = re.sub(r"\([^)]*\)", "", match.group('longname'))
      name = re.sub(r"\(.*?\)", "", match.group('longname'))
      desc = match.group('longname') + match.group('desc')
      desc = re.sub(r"&", "&amp;", desc)
      desc = re.sub(r"<", "&lt;", desc)
      desc = re.sub(r">", "&gt;", desc)
      desc = re.sub(r"^", "<p>", desc)
      desc = re.sub(r"$", "</p>", desc)
      desc = re.sub(r"\ ", "&nbsp;", desc)
      # print("************")
      # print("longname: " + match.group('longname') + " -> name: " + name)
      # print("Name:" + name)
      # print("Desc:" + desc)
      # print("************")
      registers[name] = desc

def find_register(name):
   match = next((val for key, val in registers.items() if name in key), None)
   try:
      match = next(val for key, val in registers.items() if name in key)
   except StopIteration:
      match = "Register not found"
   return match

def find_csr_desc(name, csr_file):
   try:
      desc = registers[name]
   except KeyError:
      try:
         with open(csr_file) as file:
            parse_csr_file(csr_file)
            # print("Just parsed")
      except IOError:
         return("Cannot open file" + csr_file)
   except:
      print("Unhandled exception")
      raise
      
   return(find_register(name))

class CavmCsrPopupCommand(sublime_plugin.TextCommand):
   def run(self, edit):
      for region in self.view.sel():
         if region.empty():
            return

      sel = self.view.substr(region)
      match = re.search(r'(\w+?)\_', sel)
      if match:
         blk = match.group(1).lower()
         # print("blk: " + blk)
         match = re.search(r'(.*/[to]\d+/)', self.view.file_name())
         if match:
            csr_file = match.group(1) + 'rtl/' + blk + '/' + blk + '.csr.txt'
            # print("csr_file: " + csr_file)
            result = find_csr_desc(self.view.substr(region), csr_file)
         else:
            result = "Cannot find path from " + self.view.file_name()
      else:
         result = "Cannot find block name from " + self.view.substr(region)

      if result:
         s = '<style> p {color: black; font-family: monospace;} </style>' + result
         self.view.show_popup(s, max_width=1000, max_height=400, on_navigate=print)
         # print("OK")
         # print("############")
         # print("Name:" + name)
         # print("Desc:" + desc)
         # print("############")