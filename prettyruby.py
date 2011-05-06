import sublime, sublime_plugin, re

class PrettyrubyCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    region = sublime.Region(0L, view.size())

    reformatter = RubyFormatter(view.substr(region))
    beautified = reformatter.run()

    view.replace(edit, region, beautified) 


# port from http://neontology.com/2006/05/10/beautiful-ruby-in-textmate
class RubyFormatter:
    outdentExp = [
        re.compile(r"^rescue\b"), 
        re.compile(r"^ensure\b"),
        re.compile(r"^elsif\b"),
        re.compile(r"^end\b"),
        re.compile(r"^else\b"),
        re.compile(r"\bwhen\b"),
        re.compile(r"^[^\{]*\}"),
        re.compile(r"^[^\[]*\]")]

    indentExp = [
        re.compile(r"^module\b"),
        re.compile(r"^class\b"),
        re.compile(r"^if\b"),
        re.compile(r"(=\s*|^)until\b"),
        re.compile(r"(=\s*|^)for\b"),
        re.compile(r"^unless\b"),
        re.compile(r"(=\s*|^)while\b"),
        re.compile(r"(=\s*|^)begin\b"),
        re.compile(r"(^| )case\b"),
        re.compile(r"\bthen\b"),
        re.compile(r"^rescue\b"),
        re.compile(r"^def\b"),
        re.compile(r"\bdo\b"),
        re.compile(r"^else\b"),
        re.compile(r"^elsif\b"),
        re.compile(r"^ensure\b"),
        re.compile(r"\bwhen\b"),
        re.compile(r"\{[^\}]*$"),
        re.compile(r"\[[^\]]*$")]
    def __init__(self, file_string):
        self.file_string = file_string

    def run(self):
        return self.beautify(self.file_string)
    

    def rb_make_tab(self, tab):
        return "" if tab < 0 else " " * 2 * tab
    
    def rb_add_line(self, line, tab):
        line = line.rstrip().lstrip()
        line = self.rb_make_tab(tab) + line if len(line) > 0 else line
        return line

    def beautify(self, ugly):     
        comment_block = False
        in_here_doc = False
        here_doc_term = ""
        program_end = False
        multiLine_array = []
        multiLine_str = ""
        tline = ""
        tab = 0
        output = []  

        for line in ugly.splitlines(False):
            line = line.rstrip() #better strip begin and end

            if re.match("__END__$", line):
                program_end = True
            else:
                if((not re.match("\s*#", line)) and re.search("[^\\\]\\\s*$", line)):
                    multiLine_array.append(line)
                    multiLine_str += re.sub("^(.*)\\\s*$","\\1", line)
                    next
                if len(multiLine_str) > 0:
                  multiLine_array.append(line)
                  multiLine_str += re.sub("^(.*)\\\s*$","\\1", line)
                
                tline = (multiLine_str if len(multiLine_str) > 0 else line).lstrip()

                if re.match("=begin", tline):
                  comment_block = True
                if in_here_doc:
                    if re.search("\s*" + here_doc_term + "\s*", tline):
                        in_here_doc = False 
                else: 
                  if re.search("=\s*<<", tline):
                     here_doc_term = re.sub(".*=\s*<<-?\s*([_|\w]+).*","\\1", tline)
                     in_here_doc = len(here_doc_term) > 0
            
            if comment_block or program_end or in_here_doc:
                output.append(line)
            else:
                comment_line = re.match("^#", tline)
                if not comment_line:
                    # delete end-of-line comments
                    tline = re.sub(r"#[^\"]+$","", tline)
                    # convert quotes
                    tline = re.sub(r"\\\"","'", tline)
                    
                    for oe in RubyFormatter.outdentExp:
                        if oe.match(tline):
                            tab -= 1
                            break
                if len(multiLine_array) > 0:
                    for ml in multiLine_array:
                        output.append(rb_add_line(ml, tab))
                    multiLine_array.clear
                    multiLine_str = ""
                else:
                    output.append(self.rb_add_line(line, tab))

                if not comment_line:
                    endExp = re.compile(r"\s+end\s*$")
                    for ire in RubyFormatter.indentExp:
                        if ire.search(tline) and not endExp.search(tline):
                            tab += 1
                            break
            if re.match("=end", tline):
                comment_block = False
        error = tab != 0
        if error:
            print "Error: indent/outdent mismatch: %d" %(tab)
        
        return '\n'.join(output) + "\n"
