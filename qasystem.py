import paramiko
import json
import re
import wikipedia as wiki
import requests
import logging

from wikipedia.exceptions import DisambiguationError

logger = logging.getLogger(__name__)

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

'''
{'answer': {'ans_type_pred_cls': 1, 
            'answer_type_logits': [0.46426963806152344, 3.712430477142334, 0.452737420797348, 
                                   -15.273842811584473, -14.505642890930176], 
            'answer_type_probs': [0.03606009483337402, 0.9282933473587036, 0.03564663231372833,
                                  5.272926095756247e-09, 1.1367807140061359e-08], 
            'best_span': [147, 148], 'best_span_orig': [547, 548], 
            'best_span_scores': 8.108234405517578, 'best_span_str': 'John Williams,'}, 
 'question': 'Who wrote the music to Star Wars?', 'str': 'html:The Star Wars franchise h'
                                                         'as spawned multiple live-'}
'''


def find_long_ans(span, html):
    # special_token_pos = _SPECIAL_TOKENS_RE.finditer(html)
    html_tokens = html.split(' ')
    special_token_pos = [i for i, token in enumerate(html_tokens) if _SPECIAL_TOKENS_RE.match(token)]
    for i in range(1, len(special_token_pos)):
        if special_token_pos[i-1] <= span[0] and special_token_pos[i] >= span[1]:
            la = special_token_pos[i-1], special_token_pos[i] - 1
            long_ans = ' '.join(html_tokens[la[0]: la[1] + 1])
            return long_ans, la
    return "N/A. Can't map back to a long ans", (-1,-1)



def post_process(js, html):
    # js = json.loads(raw_output)
    ans = js['answer']
    answerability_probs = ans['answer_type_probs'][:3]
    sa_span = ans['best_span_orig']
    short_ans = ans['best_span_str']
    if short_ans == '':
        short_ans = long_ans = "No answer found on the page."
        yn_probs = None
        return short_ans, long_ans, answerability_probs, yn_probs

    long_ans, la_span = find_long_ans(sa_span, html)
    # yn_probs = ans['yn_probs']
    # yn_ans = ans['yn_ans']
    yn_probs = '1 1 1'
    yn_ans = 'NONE'
    if yn_ans != 'NONE':
        short_ans = yn_ans
    if la_span[0] == sa_span[0] - 1 and la_span[1] == sa_span[1]:
        short_ans = "No short answer."

    return short_ans, long_ans, answerability_probs, yn_probs



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
        # self.use_text = True
        self.use_text = False
        logging.info(f'We only use text on the wikipedia page: {self.use_text}')

    def __del__(self):
        self.trans.close()

    def ask(self, question: str = "Why is the sky blue?"):
        # prefix = '''curl -X POST --header "Content-Type: application/json" --data \''''
        # postfix = '''\' 127.0.0.1:5666/predict'''
        # prefixf = '''curl -X POST --header "Content-Type: application/json" --data @'''
        # postfixf = ''' 127.0.0.1:5666/predict'''
        logging.info(question)
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
        logging.info(cleaned_html[:50])
        # js_str = json.dumps(js, ensure_ascii=False)
        # with open('D://body.json', 'w', encoding='utf-8') as f:
        #     f.write(js_str)
        # remotepath = '/home/sunxy-s18/data/demo/body.json'
        # self.sftp.put(localpath='D://body.json', remotepath=remotepath)
        # print(js_str)
        # # cmd = prefix + js_str + postfix
        # cmdf = prefixf + remotepath + postfixf
        # print(cmdf)
        # stdin, stdout, stderr = self.ssh.exec_command(cmdf)
        # raw_output = stdout.read().decode()
        returned = requests.post('http://localhost:5667/predict', json=js)
        returned_js = returned.json()
        print(returned_js)
        print(type(returned_js))
        sa, la, prob_ans, prob_yn = post_process(returned_js, cleaned_html)
        # return_str = page.title + '\t' + page.url + '\n' + ans
        return_str = f'Most related entry: \t{page.title} \n URL: \t{page.url}\n\n ' \
                     f'Answerbility score [no-ans vs short vs long]: {prob_ans}\n\n' \
                     f'Long answer: {la}\n\n' \
                     f'Short answer: {sa}\n\n' \
                     f'Yes/no answer [None vs Yes vs No]: {prob_yn}'
        return return_str
        # return json.dumps(res, ensure_ascii=False)

if __name__ == '__main__':
    # qa = QAsystem()
    html = wiki.page('List of rivers by length').html()
    clean = clean_html(html)
    print(find_long_ans((88, 92), clean))
    # page = get_wiki_page('mariachi')
    # html = page.html()
    # print(qa.ask())
    # print(qa.ask('Who wrote the music to Star Wars?'))



#  88 92