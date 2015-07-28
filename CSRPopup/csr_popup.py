import sublime, sublime_plugin
import subprocess
import re
import os
import fnmatch

# Caveat: different worksets may have different CSR set-up. Currently
# this doesn't check again once wks_path is set.
# Enhancement: reset on seeing different filename/path.

# Caveat: for generic name CSR (i.e. the ones without block names),
# currently this will always try to find from vkits/csr/gen files.
# Enhancement: create reg class or use multiple entry dict instead
# of current simple reg_dict that will contain generic/all information
# of a register.

# Caveat: if there's secure/non-secure reg with the same name, it'll
# show both the 1st time around (due to found 2 entries in vkits/csr/gen).
# But it'll show only 1 the next time around (due to optimization).
# Enhancement: do we need to?

def find_file_pattern(pattern, path):
    result = []
    # print("*** find_file_pattern " + pattern + " in path " + path)
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def parse_csr_file(fname, reg_dict):
   # print("*** parse_csr_file " + fname)
   flines = ''
   with open(fname, "r") as f:
      flines = str(f.read())
   parse_csr(flines, reg_dict)

def parse_csr(flines, reg_dict):
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
      # desc = re.sub(r"^", "<p>", desc)
      # desc = re.sub(r"$", "</p>", desc)
      desc = re.sub(r"\ ", "&nbsp;", desc)
      # print("************")
      # print("longname: " + match.group('longname') + " -> name: " + name)
      # print("Name:" + name)
      # print("Desc:" + desc)
      # print("************")
      reg_dict[name] = desc

def find_reg_in_dict(name, reg_dict):
   match = next((val for key, val in reg_dict.items() if name in key), None)
   try:
      match = next(val for key, val in reg_dict.items() if name in key)
   except StopIteration:
      match = "<p>Register " + name + " not found in dictionary</p>"
   return match

def find_reg_in_csr(reg, csr_file, reg_dict):
   try:
      with open(csr_file) as file:
         parse_csr_file(csr_file, reg_dict)
         # print("Just parsed")
   except IOError:
      return("Cannot open file" + csr_file)
   return(find_reg_in_dict(reg, reg_dict))

def find_csr_file(blk, csr_list):
   blk_csr = blk + ".csr.txt"
   # print("*** find_csr_file " + blk_csr)
   match = None
   for file in csr_list:
      match = re.search(blk_csr, file)
      if match:
         return(file)
   return(match)

def find_reg(reg, wks_path, csr_list, blk_dict, reg_dict):
   xreg = '$' + reg
   # print("xreg " + xreg + " *** " + reg)
   if xreg in reg_dict:
      return(find_reg_in_dict(xreg, reg_dict))

   reg_class = reg.lower() + '_reg_c';
   csr_gen_files = wks_path + "/verif/vkits/csr/gen/*"
   try:
      proc = subprocess.Popen('/bin/grep "class ' + reg_class + '" ' + csr_gen_files,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
      out,err = proc.communicate()
   except:
      return("<p>Unexpected error while building register name " + reg + " in " + wks_path + "</p>")

   sout = out.decode("utf-8")
   # print("Grep ###" + sout + "###")
   if sout == "":
      return("<p>Register name " + reg + " not found in any csr gen files in " + wks_path + "</p>")

   desc = ''
   lines = sout.split(';')
   for line in lines:
      # print("Line " + line)
      item = re.search(r'csr_(\w+?)_', line)
      if item:
         found = False
         blk = item.group(1)
         if blk in blk_dict:
            xreg = '$' + reg
            xblk = '$' + blk.upper() + "_" + reg
            if xreg in reg_dict:
               desc = desc + find_reg_in_dict(xreg, reg_dict) + "<p></p>"
               found = True
            elif xblk in reg_dict:
               desc = desc + find_reg_in_dict(xblk, reg_dict) + "<p></p>"
               found = True
         if found == False:
            csr_file = find_csr_file(blk, csr_list)
            if csr_file == None:
               desc = desc + "<p>Block name " + blk + " not found in csr_list for register name " + reg + "</p>"
            else:
               # print("blk " + blk)
               # print("csr_file " + csr_file)
               blk_dict[blk] = True
               desc = desc + find_reg_in_csr(reg, csr_file, reg_dict) + "<p></p>"

   return(desc)

def find_wks_path(filename):
   wks_path = ""
   match = re.search(r'(.*)/verif', filename)
   if match:
      wks_path = match.group(1)
      # print("wks_path: " + wks_path)
   return(wks_path)

class CavmCsrPopupExpCommand(sublime_plugin.TextCommand):
   init = False
   wks_path = ''  # Workset path relative to the active file
   csr_list = []  # List of existing csr.txt files
   blk_dict = {}  # Dict of blocks already built
   reg_dict = {}  # Dict of registers already built

   def run(self, edit):
      for region in self.view.sel():
         if region.empty():
            return

      if self.init == False:
         sublime.status_message("First time initialization...")
         self.init = True

      msg = ''

      self.wks_path = find_wks_path(self.view.file_name())
      if self.wks_path == "":
         sublime.error_message("Cannot find workset path from current file" + self.view.file_name())
         return

      if len(self.csr_list) == 0:
         sublime.status_message("First time csr_list initialization...")
         self.csr_list = find_file_pattern('*.csr.txt', self.wks_path + '/rtl')

      msg = find_reg(self.view.substr(region),
                     self.wks_path,
                     self.csr_list,
                     self.blk_dict,
                     self.reg_dict)

      if msg:
         # print("Number of dict entry: " + str(len(self.reg_dict)))
         # for x in self.reg_dict:
         #    print("***" + x + "->" + self.reg_dict[x])
         s = '<style> p {color: black; font-family: monospace;} </style>' + msg
         self.view.show_popup(s, max_width=1000, max_height=400, on_navigate=print)
         # print("*******************************")
         # print(msg)
         # print("*******************************")
