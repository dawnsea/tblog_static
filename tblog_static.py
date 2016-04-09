# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2016 by dawnsea
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import base64
import hashlib
import git
import datetime
import time as mytime
import urllib
import shutil
import uuid
import getpass

from collections import defaultdict
import operator

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
import misaka as mk

from operator import itemgetter

import pysftp
import sys



my_config = { 'REPODIR'   : 'tblog_exam',
              'GITHUB'    : 'https://github.com/dawnsea/tblog_exam.git', 
              'DOCROOT'   : '/blog',
              'NAME'      : '[t:/]',
              'DESC'      : '[t:/] is not technology-root',
              'URL'       : 'http://www.troot.co.kr',
              'FTP'       : 'ifkn.net',
              'FTPUSER'   : 'dawnsea',
              'FTPPATH'   : 'docroot'  }

reload(sys)
sys.setdefaultencoding('utf-8')

class HighlighterRenderer(mk.HtmlRenderer):
    def blockcode(self, text, lang):
        if not lang:
            return '\n<blockquote>{}</blockquote>\n'.format(text.strip()).replace('  \n', '<br>\n').replace('\n\n', '<br>')
#            return '\n<pre><code>{}</code></pre>\n'.format(text.strip())
#            return '\n{}\n'.format(text.strip())

        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()

        return highlight(text, lexer, formatter)

renderer = HighlighterRenderer()
md = mk.Markdown(renderer, extensions=mk.EXT_AUTOLINK | mk.EXT_FENCED_CODE | mk.EXT_NO_INTRA_EMPHASIS |  mk.EXT_QUOTE)


def get_posts(tagstr = '', admin = False):
    ymlist = os.listdir(my_config['REPODIR'])
    ymlist = sorted(ymlist, reverse = True)
    
    posts = []
    for ym in ymlist:
        if os.path.isdir(my_config['REPODIR'] + '/' + ym) and ym != '.git' and ym != 'images':
            titles = os.listdir(my_config['REPODIR'] + '/' + ym)
            
            for title in titles:
                post = {}
                try:
                    f = open(my_config['REPODIR'] + '/' + ym + '/' + title, 'r')
                    subject = f.readline()
                    tag     = f.readline()
                    date    = f.readline()
                    
                    text = f.read()

                    f.close()
#                    print subject
                    
                except:
                    print 'file error'
                    continue
                    
                if tagstr != '':
                    if '태그 :' not in tag or ' ' + urllib.unquote(tagstr).encode('utf-8') not in tag:
                        continue
                    
                subject = subject.replace('제목 :', '').strip()
                date    = date.replace('날짜 :', '').strip()

                if not admin:
                    if '[비밀글]' in subject or '[비공개]' in subject:
                        continue
                
                try:
                    write_time  = mytime.strptime(date, '%Y/%m/%d')
                except:
                    print '타임 에러 %s' % subject
                    continue
                
                post['year']        = mytime.strftime('%Y', write_time)
                post['month']       = mytime.strftime('%m', write_time)
                post['day']         = mytime.strftime('%d', write_time)
                post['date']        = date   
                post['title']       = urllib.unquote(subject)
                post['filename']    = title
                post['timestamp']   = mytime.mktime(write_time)
                post['timestr']     = mytime.asctime(mytime.localtime(post['timestamp'])) + ' +0900'
                post['tags']        = tag.replace('태그 : ', '').strip().split(',')
                post['tag']         = tag.replace('태그 : ', '').strip()
                post['text']        = md(text.decode('utf-8'))
                post['text']        = post['text'].replace('</p>\n\n', '</p><br>\n').replace('img src="/', 'img src="%s/images/' % my_config['DOCROOT'])
                post['stext']        = escape(mk.html(text.decode('utf-8')[:100] + '... (RSS 생략)'))
                posts.append(post)
                
        else:
            print '제목이 없음'
    posts = sorted(posts, key=itemgetter('timestamp'), reverse = True)

    return posts

def escape(t):
    return (t
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("'", "&#39;").replace('"', "&quot;")
        )

def git_clone():
    
    git.Git().clone(my_config['GITHUB'])
    
def git_pull():
    git.cmd.Git(my_config['REPODIR']).pull()
    

def gen_deploy():
    try:
        shutil.rmtree('deploy')
    except:
        pass
        
    try:
        os.makedirs('deploy/tag')
    except:
        pass

    shutil.copytree('templates/css', 'deploy/css')
    shutil.copytree('%s/images' % my_config['REPODIR'], 'deploy/images')
    
def get_layout(title = '', body = ''):
    f = open('templates/header.html', 'r')
    ret = f.read()
    f.close()
    
    if title != '':
        ret = ret.replace('##title##', title)
        
    if body != '':
        ret = ret.replace('##body##', body)
    
    return ret.strip().replace('##docroot##', my_config['DOCROOT']);
    
def get_front(posts):
    f = open('templates/front.html', 'r')
    ret = f.read().strip()
    f.close()
    
    front_list = ''
    
    for post in posts:
        if '[비공개]' in post['title'] or '[비밀글]' in post['title']:
            class_name = 'class="admin"'
        else:
            class_name = 'class="uline"'
        front_list = front_list + '<li><a %s href="%s/%s/%s/%s.troot">%s</a><span class=date>%s</span></li>\n' % \
                        (class_name, my_config['DOCROOT'], post['year'], post['month'], urllib.quote(post['filename']), post['title'].decode('utf8'), post['date'])
        
#       {{ url_for('view', year=post.year, month=post.month, filename=post.filename.decode('utf-8'))}}">{{ post.title.decode('utf8') }}</a><span class=date>{{ post.date }}</span></li>

    return ret.replace('##list##', front_list).replace('##count##', str(len(posts))).strip()
    
def deploy_file(filename, text):
    f = open(filename, 'w')
    f.write(text)
    f.flush()
    f.close()
  

def gen_guest():
    f = open('templates/guest.html', 'r')
    guest = f.read()
    f.close()
    
    body = get_layout(title = '방명록', body = guest)
    deploy_file('deploy/guest', body)
    
def gen_rss(posts):
        
    f = open('templates/rss.xml', 'r')
    rss = f.read()
    f.close()
    
    rss = rss.replace('##name##', my_config['NAME']).replace('##url##', my_config['URL']).replace('##desc##', my_config['DESC'])
    rss = rss.replace('##pubdate##', datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900"))
    
    index = 0
    
    itemstr = ''
    for post in posts:
        itemstr = itemstr + \
                      '     <item>\n' \
                      '         <title>%s</title>\n' \
                      '         <link>%s%s/%s/%s/%s</link>\n' \
                      '         <description>%s</description>\n' \
                      '         <pubDate>%s</pubDate>\n' \
                      '     </item>\n' % (post['title'].decode('utf-8'), my_config['URL'], my_config['DOCROOT'], post['year'], post['month'], post['filename'], post['stext'], post['timestr'])
        
        if index > 10:
            break
        index = index + 1
        
    rss = rss.replace('##itemstr##', itemstr)
    deploy_file('deploy/rss.xml', rss)
    

def gen_tagall(posts):
    
    gtags = defaultdict(lambda: 1)

    for post in posts:
        for tag in post['tags']:

            tag = tag.strip()

            if tag is not '':
                gtags[tag] = gtags[tag] + 1

    gtags = sorted(gtags.items(), key=operator.itemgetter(0), reverse = False)
    
    f = open('templates/tagall.html', 'r')
    tagall = f.read()
    f.close()
    
    tagstr = ''
    for tag in gtags:
        tagstr = tagstr + '<a class="uline" href="%s/tag/%s">%s</a><span class=date>/%s</span><br>\n' % (my_config['DOCROOT'], tag[0], tag[0], tag[1] - 1)
        
    tagall = tagall.replace('##tagall##', tagstr)   
    
    body = get_layout(title = '태그에 의한 분류', body = tagall)
    deploy_file('deploy/tagall', body)


def gen_tags(posts):
    
    body = get_layout()
    
    tag_list = set('')
    for tag in posts:
    
        for tag_single in tag['tags']:
            tag_list.add(tag_single.strip())
            
    for tag_single in tag_list:
        
        if tag_single.strip() == '':
            continue
        
        post_result = []            
        for post in posts:
            
            if tag_single in post['tag']:
                post_result.append(post)
        
        view_result = body.replace('##title##', tag_single).replace('##body##', get_front(post_result)).replace('##docroot##', my_config['DOCROOT'])
        deploy_file('deploy/tag/%s' % (tag_single), view_result)

                





#       break;
#    print(str(tag_list))

        
    
def gen_sub(posts):
    
    f = open('templates/content.html', 'r')
    ret = f.read().strip();
    f.close()
    
    body = get_layout()
    
    for post in posts:
        try:
            os.makedirs('deploy/%s/%s' % (post['year'], post['month']))
            
        except:
            pass
        
        result = ''
        
        result = ret.replace('##title##', post['title'])
        result = result.replace('##content##', post['text']) 
        result = result.replace('##date##', post['date'])
        result = body.replace('##title##', post['title']).replace('##body##', result).strip()
        
        itemstr = ''
        for item in post['tags']:
            itemstr = itemstr + '<a href="%s/tag/%s.troot">%s/</a> ' % ( my_config['DOCROOT'], item.strip(), item.strip())
            
        result = result.replace('##tag##', itemstr)
        
        deploy_file('deploy/%s/%s/%s.troot' % (post['year'], post['month'], post['filename']), result)
        
def gen_static():
    print '시작'
    
    gen_deploy()
    posts = get_posts(admin = True)
    
    admin_url = 'admin%s' % uuid.uuid4()
    
    front_list = get_front(posts)
    deploy_file('deploy/%s' % admin_url, get_layout(title = 'admin', body = front_list))    
    
    print 'amdin url = %s%s/%s' % (my_config['URL'], my_config['DOCROOT'], admin_url)
    print 'amdin url = http://localhost%s/%s' % (my_config['DOCROOT'], admin_url)
    
    gen_sub(posts)
    gen_guest()
    gen_rss(posts)
    
    posts = get_posts()    
    front_list = get_front(posts)
    deploy_file('deploy/index.html', get_layout(title = '', body = front_list))    
    gen_tagall(posts)
    gen_tags(posts)    
    
    
    
if __name__ == '__main__':  

    print '사용법 : tblog_statc.py clone | pull\n'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clone':
            git_clone()
        if sys.argv[1] == 'pull':
            git_pull()    
    else:
        gen_static()
    
        print '%s/deploy' % os.getcwd()
    
        pw = getpass.getpass("ftp %s password : " % my_config['FTP'])
        
        with pysftp.Connection(my_config['FTP'], username = my_config['FTPUSER'], password = pw) as sftp:
            for filename in sftp.listdir(my_config['FTPPATH']):
                if 'admin' in filename:
                    print '%s/%s' % (my_config['FTPPATH'], filename)
                    sftp.remove('%s/%s' % (my_config['FTPPATH'], filename))

            sftp.put_r('%s/deploy' % os.getcwd(), my_config['FTPPATH'], confirm = True, preserve_mtime = True)

