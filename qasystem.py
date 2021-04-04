import paramiko
import json
import re
import wikipedia as wiki
import requests
import logging

from wikipedia.exceptions import DisambiguationError

requests.adapters.DEFAULT_RETRIES = 5

# 将sshclient的对象的transport指定为以上的trans

# 执行命令，和传统方法一样
# stdin, stdout, stderr = ssh.exec_command('ls')
# print(stdout.read().decode())

_SPECIAL_TOKENS_RE = re.compile(r"^\[[^ ]*\]$", re.UNICODE)
tags_to_keep = ["<Table>", "<P>", "<Ul>", "<Dl>", "<Ol>", "<Tr>", "<Li>", "<Dd>", "<Dt>"]
_HTML_TOKENS_RE = re.compile(r"^<[^ ]*>$", re.UNICODE)
_HTML_TAGS_RE = re.compile(r"<[^>]*>", re.UNICODE)


def get_wiki_page(question):
    related_entries = wiki.search(question)
    if len(related_entries) > 0:
        page = wiki.page(related_entries[0])
        return page
    else:
        return None

def clean_html(html):
    html = _SPECIAL_TOKENS_RE.sub(' ', html)
    html = re.sub('<p>', '[Paragraph] ', html)
    html = re.sub('<Table>', '[Table] ', html)
    html = re.sub('<Ul>', '[List] ', html)
    html = re.sub('<Dl>', '[List] ', html)
    html = re.sub('<Ol>', '[List] ', html)
    html = _HTML_TAGS_RE.sub(' ', html)
    html = re.sub('-', ' - ', html)
    html = re.sub(r"\'", "'", html)
    html = re.sub(r'&#91;\d+&#93;', ' ', html)
    html = re.sub(r'&#\d*;', ' ', html)
    html = re.sub('([.,!?()])', r' \1 ', html)
    html = re.sub('\s{2,}', ' ', html)
    html = re.sub(r'\[ edit \]', ' ', html)
    return html


def post_process(raw_output):
    js = json.loads(raw_output)
    ans = js['answer']['best_span_str']
    if ans == '':
        return "No answer found on the page.", 0
    return ans, 1



class QAsystem(object):
    def __init__(self):
        trans = paramiko.Transport(('10.134.171.215', 2222))
        # 建立连接
        trans.connect(username='sunxy-s18', password='xiaoyu123')
        ssh = paramiko.SSHClient()
        ssh._transport = trans
        sftp = paramiko.SFTPClient.from_transport(trans)
        # 发送文件

        self.ssh = ssh
        self.trans = trans
        self.sftp = sftp
        # use text or html
        self.use_text = True
        logging.info(f'We only use text on the wikipedia page: {self.use_text}')

    def __del__(self):
        self.trans.close()

    def ask(self, question: str = "Why is the sky blue?"):
        prefix = '''curl -X POST --header "Content-Type: application/json" --data \''''
        postfix = '''\' 127.0.0.1:5666/predict'''
        prefixf = '''curl -X POST --header "Content-Type: application/json" --data @'''
        postfixf = ''' 127.0.0.1:5666/predict'''
        try:
            page = get_wiki_page(question)
        except DisambiguationError as e:
            return f'Your question is ambiguous.\n{e.title} may refer to: {e.options}'
        if not page:
            return 'No related Wikipedia pages are found.\n You may consider another question or refer to an example on the home page.'
        # html = '<html><\html><html><\html><html><\html><html><\html>'
        # todo
        if self.use_text:
            cleaned_html = page.content
        else:
            html = page.html()
            cleaned_html = clean_html(html)
        js = {
            "question": question,
            "html": cleaned_html,
        }
        print(cleaned_html[:20])
        js_str = json.dumps(js, ensure_ascii=False)
        with open('D://body.json', 'w', encoding='utf-8') as f:
            f.write(js_str)
        remotepath = '/home/sunxy-s18/data/demo/body.json'
        self.sftp.put(localpath='D://body.json', remotepath=remotepath)
        print(js_str)
        # cmd = prefix + js_str + postfix
        cmdf = prefixf + remotepath + postfixf
        print(cmdf)
        stdin, stdout, stderr = self.ssh.exec_command(cmdf)
        raw_output = stdout.read().decode()
        print(raw_output)
        ans, confidence = post_process(raw_output)
        return_str = page.title + '\t' + page.url + '\n' + ans
        return_str = f'Most related entry: {page.title} at {page.url}\n Answer: {ans}\n Confidence: {confidence}'
        return return_str
        # return json.dumps(res, ensure_ascii=False)

if __name__ == '__main__':
    qa = QAsystem()
    page = get_wiki_page('mariachi')
    html = page.html()
    # print(qa.ask())
    # print(qa.ask('Who wrote the music to Star Wars?'))



