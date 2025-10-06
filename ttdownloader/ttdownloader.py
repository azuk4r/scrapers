from json import load,dump,JSONDecodeError
from datetime import datetime,timezone
from argparse import ArgumentParser
from urllib.parse import urlparse
from os.path import join,abspath
from requests import Session
from random import uniform
from re import search,sub
from os import makedirs
from time import sleep
from tqdm import tqdm
from sys import exit

AID=1988;COUNT=35;LANG='en'

def log(msg): print(f'\033[31m[ttdownloader]\033[0m {msg}')

def init_session(proxy=None):
	session=Session()
	session.headers.update({
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
		'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language':'en-US,en;q=0.5',
		'Referer':'https://www.tiktok.com/',
		'Connection':'keep-alive',
		'Upgrade-Insecure-Requests':'1',
		'Range':'bytes=0-'})
	if proxy:
		if '@' in proxy:
			parsed=urlparse(proxy)
			proxy=f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
		session.proxies.update({
			'http':proxy,
			'https':proxy})
	return session

def get_secuid_and_print_cookies(profile_url,session):
	log('accessing profile to get secUid and cookies...')
	profile_response=session.get(profile_url)
	if profile_response.status_code not in (200,206):
		log(f'error accessing profile: {profile_response.status_code}')
		exit()
	html=profile_response.text
	match=search(r'"secUid"\s*:\s*"([^"]+)"',html)
	if not match:
		log('secUid not found in profile page. exiting.')
		exit()
	secuid=match.group(1)
	log(f'secUid: {secuid}')
	for cookie in session.cookies:log(f'{cookie.name}: {cookie.value}')
	return secuid	# no need to return cookies bcoz requests.Session keeps them alive

def fetch_posts(secuid,session,log_once):
	if not log_once['retrieving_posts']:
		log('retrieving posts...')
		log_once['retrieving_posts']=True
	all_posts=[]
	cursor='0'
	while True:
		posts_url=f'https://www.tiktok.com/api/post/item_list/?secUid={secuid}&aid={AID}&count={COUNT}&cursor={cursor}&language={LANG}'
		response=session.get(posts_url)
		if response.status_code not in (200,206):
			log(f'error fetching posts: {response.status_code}')
			sleep(uniform(1,3))
			continue
		try:data=response.json()
		except Exception:continue
		items=data.get('itemList',[])
		if not items:
			if not log_once['no_posts']:
				log('total posts retrieved: 0')
				log_once['no_posts']=True
			sleep(uniform(1,3))
			return None
		all_posts.extend(items)
		if not data.get('hasMore',False):break
		cursor=str(data.get('cursor','0'))
		log(f'total posts retrieved: {len(all_posts)}')
	log(f'total posts retrieved: {len(all_posts)}')
	return all_posts

def download(url,filepath,session):
	while True:
		try:
			with session.get(url,stream=True) as response:
				if response.status_code in (200,206):
					with open(filepath,'wb') as f:
						for chunk in response.iter_content(chunk_size=8192):f.write(chunk)
					return True
				else:pass
		except Exception:sleep(uniform(1,3))

def save_json(result_data,username,download_dir):
	json_filename=join(download_dir,f'{username}_posts.json')
	with open(json_filename,'w',encoding='utf-8') as f:dump(result_data,f,ensure_ascii=False,indent=4)

def process_posts(posts,session,download_dir,result_data):
	log('downloading media...')
	author=posts[0].get('author',{})
	unique_id=author.get('uniqueId','unknown_user')
	makedirs(join(download_dir,unique_id),exist_ok=True)
	existing_urls=set()
	for post_data in result_data[unique_id]['posts'].values():
			urls=post_data['url'].split('?')[0]
			if not isinstance(urls,list):urls=[urls]
			existing_urls.update(urls)
	for index,post in enumerate(tqdm(posts,unit='post',ncols=80),1):
		post_id=post.get('id')
		timestamp=post.get('createTime')
		create_time_str=datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat() if timestamp else None
		desc=post.get('desc','')
		stats=post.get('stats',{})
		safe_post_id=sub(r'[^\w\-]','_',post_id)
		time_component=str(timestamp or '0')
		post_key=str(index)
		image_post=post.get('imagePost')
		if image_post and 'images' in image_post and image_post['images']:
			url_entries=[];image_entries=[]
			for i,image_info in enumerate(image_post['images'],1):
				urls=image_info.get('imageURL',{}).get('urlList',[])
				if not urls:continue
				img_url=urls[0]
				if not img_url.startswith('https://p16'):continue
				if img_url.split('?')[0] in existing_urls:continue
				ext=img_url.split('?')[0].split('.')[-1]
				filename=f'{safe_post_id}_{time_component}_{i}.{ext}'
				filepath=join(download_dir,unique_id,filename)
				full_path=abspath(filepath)
				if download(img_url,filepath,session):
					url_entries.append(img_url)
					image_entries.append(full_path)
			if image_entries:
				result_data[unique_id]['posts'][post_key]={
					'type':'images',
					'url':url_entries,
					'local_paths':image_entries,
					'desc':desc,
					'create_time':create_time_str,
					'stats':stats}
				save_json(result_data,unique_id,download_dir)
			continue
		video=post.get('video',{})
		video_url=video.get('playAddr') or ''
		if video_url.startswith('https://v16'):
			if video_url.split('?')[0] in existing_urls:continue
			filename=f'{safe_post_id}_{time_component}.mp4'
			filepath=join(download_dir,unique_id,filename)
			full_path=abspath(filepath)
			if download(video_url,filepath,session):
				result_data[unique_id]['posts'][post_key]={
					'type':'video',
					'url':video_url,
					'local_path':full_path,
					'desc':desc,
					'create_time':create_time_str,
					'stats':stats}
				save_json(result_data,unique_id,download_dir)

def main():
	parser=ArgumentParser(description='tiktok profile media downloader')
	parser.add_argument('profile_url',help='tiktok profile url')
	parser.add_argument('--download_path',default='downloads',help='custom directory to save media')
	parser.add_argument('--proxy',default=None,help='optional proxy url')
	args=parser.parse_args()
	profile_url=args.profile_url.strip('/')
	download_dir=args.download_path
	proxy=args.proxy
	session=init_session(proxy)
	log(f'current ip: {session.get("https://api.ipify.org").text}')
	secuid=get_secuid_and_print_cookies(profile_url,session)
	log_once={'no_posts':False,'posts_retrieved':False,'retrieving_posts':False}
	all_posts=None
	while not all_posts:all_posts=fetch_posts(secuid,session,log_once)
	result_data={}
	author=all_posts[0].get('author',{})
	unique_id=author.get('uniqueId','unknown_user')
	json_filename=join(download_dir,f'{unique_id}_posts.json')
	try:
		with open(json_filename,'r',encoding='utf-8') as f:result_data=load(f)
	except (FileNotFoundError,JSONDecodeError):
		result_data[unique_id]={
			'uniqueId':unique_id,
			'nickname':author.get('nickname'),
			'avatar':author.get('avatarLarger'),
			'privateAccount':author.get('privateAccount'),
			'verified':author.get('verified'),
			'secUid':author.get('secUid'),
			'signature':author.get('signature'),
			'posts':{}}
	process_posts(all_posts,session,download_dir,result_data)
	log('process finished.')

if __name__ == '__main__':main()
	# by azuk4r
	# ¬_¬
