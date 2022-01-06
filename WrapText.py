import re

re_split = re.compile('\n\s*\n')
re_sub = re.compile('([^\s])\s*\n(\s*)([^\s])')
re_find = re.compile('[^\s]\s+')
re_leading = re.compile('^\s*')
re_trailing = re.compile('\s*$')
    
def par_repl(m):
    spaces = m.group(2)
    if not spaces:
        spaces = ' '
    return m.group(1)+spaces+m.group(3)

def wrap(text,width=80,strip_leading_spaces=True,strip_trailing_spaces=True):
    
    if strip_leading_spaces:
        text = re_leading.sub('',text)
    if strip_trailing_spaces:
        text = re_trailing.sub('',text)

    paragraphs=[]
    for paragraph in re_split.split(text):
        paragraph = re_sub.sub(par_repl,paragraph)

        lines = []
        marker = 0
        pos = 0
        for item in re_find.finditer(paragraph+' '):
            newpos = item.start()
            if (newpos-marker)>=width and pos>marker:
                lines.append(paragraph[marker:pos])
                marker=pos+1
            pos = item.end()-1            
        if(marker<len(paragraph)):
            lines.append(paragraph[marker:])
        if not lines:
            lines = [paragraph]
        
        paragraphs.append("\n".join(lines))
    return "\n\n".join(paragraphs)