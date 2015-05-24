import sublime, sublime_plugin
import webbrowser
import re

WIKI_URL = r"http://mawiki.caveonetworks.com/wiki"

class CavmCsrOpenUrlCommand(sublime_plugin.TextCommand):
   def run(self, edit):
      for region in self.view.sel():
         if not region.empty():
            fn = self.view.file_name()
            # print("file_name: ", fn)
            match = re.search(r'/[to](\d+)/verif/', fn)
            if not match:
               return
            project = "rfif" #match.group(1) + "xx"
            # print("project: ", project)
            
            sel = self.view.substr(region)
            match = re.search(r'(\w+?)\_', sel)
            if not match:
               return
            blk = match.group(1)
            # print("blk: ", blk)

            url = WIKI_URL + "/" + project + "/" + blk + "/" + "CSR\#" + sel
            print("url: ", url)
            webbrowser.open_new_tab(url)
