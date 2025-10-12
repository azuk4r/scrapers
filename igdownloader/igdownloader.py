from ffmpeg import input as ffin,probe as ffprobe,output as ffout
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome,ChromeOptions
from os.path import join,abspath,exists,getsize
from tempfile import mkdtemp,TemporaryDirectory
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from argparse import ArgumentParser
from random import uniform,randint
from urllib.parse import urlparse
from json import load,dump
from re import sub,match
from requests import get
from pathlib import Path
from os import makedirs
from time import sleep
from json import loads

PROXIES={};BATCH=999;W,H=1920,1080;DBG=False;PROXY_ARGS=[];VID_COUNTER=1
DARK='\033[38;2;140;140;140m';RED='\033[31m';PINK='\033[38;2;255;20;147m';RESET='\033[0m'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
CH_BRANDS=[{'brand':'Not)A;Brand','version':'8'},{'brand':'Chromium','version':'138'},{'brand':'Google Chrome','version':'138'}]

hsleep=lambda a=1,b=2:sleep(uniform(a,b))
media_key=lambda u:sub(r'https?://[^/]+','',u.split('?',1)[0])	# strip domain and query from media url
is_pp=lambda u:any(t in u for t in ('/v/t51.2885-19/','/v/t51.75761-19/'))	# detect profile pic url
uname=lambda u:match(r'https?://(?:www\.)?instagram\.com/([^/?#]+)/?',u).group(1)	# extract username
clean=lambda u:f'{u.split("?",1)[0]}?{"&".join(q for q in u.split("?",1)[1].split("&") if not q.startswith(("bytestart","byteend")))}'if'?'in u else u	# clean media url

def dbg(t): print(t) if DBG else None
def get_idx(j): return 1 if not j else max(p['post_idx'] for p in j) + 1
def load_json(p): return load(open(p,encoding='utf-8')) if exists(p) else []
def save_json(p,d): dump(d,open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
def get_seen(j): return {m['media_key'] for p in j for x in ('pics','vids') for m in p.get(x,[]) if m.get('media_key')}
def get_hrefs(j): return {p['href'] for p in j if 'post_idx' in p and p.get('post_idx') is not None and 'href' in p and p['href']}
def is_video(f): return bool(f) and exists(f) and getsize(f)>16*1024 and any(s['codec_type']=='video' for s in ffprobe(f)['streams'])

def stealth():	# js stealth
	return f'''
	Object.defineProperty(navigator,'plugins',{{get:()=>[]}});
	Object.defineProperty(navigator,'mimeTypes',{{get:()=>[]}});
	Object.defineProperty(navigator,'deviceMemory',{{get:()=> 16}});
	Object.defineProperty(navigator,'language',{{get:()=> 'en-US'}});
	Object.defineProperty(navigator,'platform',{{get:()=> 'Win32'}});
	Object.defineProperty(navigator,'webdriver',{{get:()=>undefined}});
	Object.defineProperty(navigator,'vendor',{{get:()=> 'Google Inc.'}});
	Object.defineProperty(window,'RTCPeerConnection',{{value:undefined}});
	Object.defineProperty(navigator,'hardwareConcurrency',{{get:()=> 16}});
	Object.defineProperty(navigator,'languages',{{get:()=>['en-US','en']}});
	Object.defineProperty(window,'webkitRTCPeerConnection',{{value:undefined}});
	Object.defineProperty(window,'screen',{{value:{{width:{W},height:{H},availWidth:{W},availHeight:{H},orientation:{{type:'landscape-primary'}},colorDepth:24,pixelDepth:24}}}});
	(function(){{const o=HTMLCanvasElement.prototype.toDataURL,g=CanvasRenderingContext2D.prototype.getImageData;HTMLCanvasElement.prototype.toDataURL=function(t,q){{const c=this.getContext('2d');if(c){{const i=c.getImageData(0,0,this.width,this.height),d=i.data;for(let j=0;j<d.length;j+=4){{d[j]=(d[j]+Math.floor(Math.random()*10)-5)&255;d[j+1]=(d[j+1]+Math.floor(Math.random()*10)-5)&255;d[j+2]=(d[j+2]+Math.floor(Math.random()*10)-5)&255;}}c.putImageData(i,0,0);}}return o.call(this,t,q);}};CanvasRenderingContext2D.prototype.getImageData=function(x,y,w,h){{const i=g.call(this,x,y,w,h),d=i.data;for(let j=0;j<d.length;j+=4){{d[j]=(d[j]+Math.floor(Math.random()*6)-3)&255;d[j+1]=(d[j+1]+Math.floor(Math.random()*6)-3)&255;d[j+2]=(d[j+2]+Math.floor(Math.random()*6)-3)&255;}}return i;}}}})();
	'''

def drv(proxy=None):	# currently only chrome driver is supported
	o=ChromeOptions()
	o.add_argument('--lang=en-US')
	o.add_argument('--log-level=0')
	o.add_argument(f'user-agent={UA}')
	o.add_argument('--enable-logging')
	o.add_argument(f'--window-size={W},{H}')
	o.add_experimental_option('useAutomationExtension',False)
	o.set_capability('goog:loggingPrefs',{'performance':'ALL'})
	o.add_argument('--disable-blink-features=AutomationControlled')
	o.add_experimental_option('excludeSwitches',['enable-automation'])
	if proxy:
		try:
			parsed=urlparse(proxy)
			if parsed.hostname and parsed.port:
				if not parsed.username and not parsed.password:
					dbg(f'{DARK}[debug] proxy: {parsed.hostname}:{parsed.port}{RESET}')
					o.add_argument(f'--proxy-server={proxy}')
				else:print(f'{RED}[WARNING] currently the tool has no support for proxies with authentication for selenium (it will only use them for requests){RESET}')
			else:print(f'{RED}[error] invalid proxy format: {proxy}{RESET}')
		except Exception as e:
			print(f'{RED}[error] proxy setup: {e}{RESET}')
			o.add_argument(f'--proxy-server={proxy}')
	d=Chrome(service=Service(ChromeDriverManager().install()),options=o)
	d.set_window_size(W,H)
	d.execute_cdp_cmd('Emulation.setLocaleOverride',{'locale':'en-US'})
	d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':stealth()})
	d.execute_cdp_cmd('Emulation.setTimezoneOverride',{'timezoneId':'America/New_York'})
	d.execute_cdp_cmd('Network.setUserAgentOverride',{'userAgent':UA,'userAgentMetadata':{'brands':CH_BRANDS,'fullVersion':'138.0.0.0','platform':'Windows','platformVersion':'15.0.0','architecture':'x86','model':'','mobile':False,'bitness':'64','wow64':False}})
	return d

def dbg_stealth(d):	# dbg stealth
	urls=['https://browserleaks.com/webrtc','https://browserleaks.com/javascript','https://browserleaks.com/canvas','https://browserleaks.com/webgl']
	try:
		dbg(f'{DARK}[debug] stealth check started{RESET}')
		for url in urls:
			try:
				dbg(f'{DARK}[debug] {url.split("/")[-1]}...{RESET}')
				d.get(url)
				hsleep(3,5)
				if 'webrtc' in url:
					try:
						ipv4_element=d.find_element(By.ID,'client-ipv4')
						ip=ipv4_element.get_attribute('data-ip')
						country=ipv4_element.get_attribute('data-iso_code')
						dbg(f'{DARK}[debug] ip: {ip} ({country}){RESET}')
						leak_element=d.find_element(By.ID,'rtc-leak')
						status='no leak' if 'No Leak' in leak_element.text else 'leak'
						dbg(f'{DARK}[debug] webrtc: {status}{RESET}')
					except Exception as e:
						dbg(f'{DARK}[debug] webrtc: failed{RESET}')
				elif 'javascript' in url:
					try:
						try:d.find_element(By.CLASS_NAME,'more-button').click();hsleep(1,2)
						except:pass
						platform_element=d.find_element(By.ID,'js-platform')
						webdriver_element=d.find_element(By.ID,'js-webdriver')
						plugins_element=d.find_element(By.ID,'js-plugins')
						mimetypes_element=d.find_element(By.ID,'js-mimeTypes')
						device_memory_element=d.find_element(By.ID,'js-deviceMemory')
						language_element=d.find_element(By.ID,'js-language')
						languages_element=d.find_element(By.ID,'js-languages')
						vendor_element=d.find_element(By.ID,'js-vendor')
						hardware_element=d.find_element(By.ID,'js-hardwareConcurrency')
						width_element=d.find_element(By.ID,'js-width')
						height_element=d.find_element(By.ID,'js-height')
						avail_width_element=d.find_element(By.ID,'js-availWidth')
						avail_height_element=d.find_element(By.ID,'js-availHeight')
						color_depth_element=d.find_element(By.ID,'js-colorDepth')
						pixel_depth_element=d.find_element(By.ID,'js-pixelDepth')
						orientation_element=d.find_element(By.ID,'js-orientation-type')
						platform=platform_element.text.strip()
						webdriver=webdriver_element.text.strip()
						plugins=plugins_element.text.strip()
						mimetypes=mimetypes_element.text.strip()
						device_memory=device_memory_element.text.strip()
						language=language_element.text.strip()
						languages=languages_element.text.strip()
						vendor=vendor_element.text.strip()
						hardware=hardware_element.text.strip()
						width=width_element.text.strip()
						height=height_element.text.strip()
						avail_width=avail_width_element.text.strip()
						avail_height=avail_height_element.text.strip()
						color_depth=color_depth_element.text.strip()
						pixel_depth=pixel_depth_element.text.strip()
						orientation=orientation_element.text.strip()
						dbg(f'{DARK}[debug] platform: {platform.lower()}{RESET}')
						wd_status="hidden" if webdriver=="undefined" else "detected"
						dbg(f'{DARK}[debug] webdriver: {wd_status}{RESET}')
						dbg(f'{DARK}[debug] plugins: {plugins[:50]}...{RESET}')
						dbg(f'{DARK}[debug] mimeTypes: {mimetypes[:50]}...{RESET}')
						dbg(f'{DARK}[debug] deviceMemory: {device_memory}{RESET}')
						dbg(f'{DARK}[debug] language: {language}{RESET}')
						dbg(f'{DARK}[debug] languages: {languages}{RESET}')
						dbg(f'{DARK}[debug] vendor: {vendor}{RESET}')
						dbg(f'{DARK}[debug] hardwareConcurrency: {hardware}{RESET}')
						dbg(f'{DARK}[debug] screen: {width}x{height} ({avail_width}x{avail_height}){RESET}')
						dbg(f'{DARK}[debug] colorDepth: {color_depth}, pixelDepth: {pixel_depth}{RESET}')
						dbg(f'{DARK}[debug] orientation: {orientation}{RESET}')
					except Exception as e:dbg(f'{DARK}[debug] javascript: failed{RESET}')
				elif 'canvas' in url:
					try:
						sig_element=d.find_element(By.ID,'canvas-hash')
						uniqueness_element=d.find_element(By.ID,'canvas-ratio')
						signature=sig_element.text.strip()
						uniqueness=uniqueness_element.text.strip()
						dbg(f'{DARK}[debug] canvas: {signature}{RESET}')
						dbg(f'{DARK}[debug] canvas uniqueness: {uniqueness}{RESET}')
					except Exception as e:dbg(f'{DARK}[debug] canvas: failed{RESET}')
				elif 'webgl' in url:
					try:
						report_hash_element=d.find_element(By.ID,'gl-report-hash')
						webgl_report_hash=report_hash_element.text.strip()
						dbg(f'{DARK}[debug] webgl report hash: {webgl_report_hash}{RESET}')
						image_hash_element=d.find_element(By.ID,'gl-image-hash')
						webgl_image_hash=image_hash_element.text.strip()
						dbg(f'{DARK}[debug] webgl image hash: {webgl_image_hash}{RESET}')
						vendor_element=d.find_element(By.ID,'UNMASKED_VENDOR_WEBGL')
						renderer_element=d.find_element(By.ID,'UNMASKED_RENDERER_WEBGL')
						vendor=sub(r'!\s*','',vendor_element.text).strip()
						renderer=sub(r'!\s*','',renderer_element.text).strip()
						dbg(f'{DARK}[debug] webgl vendor: {vendor}{RESET}')
						dbg(f'{DARK}[debug] webgl renderer: {renderer}{RESET}')
					except Exception as e:dbg(f'{DARK}[debug] webgl: failed{RESET}')
				hsleep(2,4)
			except Exception as e:
				dbg(f'{DARK}[debug] {url.split("/")[-1]}: failed{RESET}')
				continue
		dbg(f'{DARK}[debug] stealth check completed{RESET}')
		return True
	except Exception as e:
		dbg(f'{DARK}[debug] stealth check: error{RESET}')
		return False

def load_cookies(d,p):
	try:
		dbg(f'{DARK}[debug] navigating to instagram...{RESET}')
		d.get('https://www.instagram.com/')
		hsleep(2,3)
		dbg(f'{DARK}[debug] loading cookies from {p}...{RESET}')
		with open(p,'r') as f:cookies=load(f)
		for cookie in cookies:
			try:
				cookie_copy=cookie.copy()
				if 'sameSite' in cookie_copy and cookie_copy['sameSite'] not in ('Strict','Lax','None'):del cookie_copy['sameSite']
				d.add_cookie(cookie_copy)
			except:continue
		dbg(f'{DARK}[debug] cookies loaded{RESET}')
		return True
	except Exception as e:print(f'{RED}[error] loading cookies: {e}{RESET}');return False

def verify_login(d):
	if not a.cookies:d.get('https://www.instagram.com/')
	while True:
		try:
			dbg(f'{DARK}[debug] checking login...{RESET}')
			elements=d.find_elements(By.XPATH,'//img[contains(@alt, "profile picture")]')
			if elements:
				dbg(f'{DARK}[debug] login successful{RESET}')
				return True
			dbg(f'{DARK}[debug] waiting for login...{RESET}')
			hsleep(2,3)
		except:hsleep(2,3);continue

def get_info(d,user):
	posts=[]
	for a in d.find_elements(By.XPATH,f'//a[contains(@href,"/{user}/")]'):
		href=a.get_attribute('href')
		parent=a.find_element(By.XPATH,'./..')
		is_clip,is_carousel,is_pinned=False,False,False
		for svg in parent.find_elements(By.TAG_NAME,'svg'):
			label=(svg.get_attribute('aria-label') or svg.get_attribute('title') or '')
			if 'Carousel' in label:is_carousel=True
			if 'Pinned' in label:is_pinned=True
			if 'Clip' in label:is_clip=True
		pic_url=None
		try:pic=a.find_element(By.TAG_NAME,'img');pic_url=pic.get_attribute('src')
		except:pass
		posts.append({'href':href,'is_clip':is_clip,'is_carousel':is_carousel,'is_pinned':is_pinned,'pic':pic_url,'element':a})
	return posts

def get_desc_and_date(d):
	description,date_iso='',''
	try:
		desc_elements=d.find_elements(By.XPATH,'//div[contains(@class,"xt0psk2")]//h1[contains(@class,"_ap3a")]')
		if not desc_elements:desc_elements=d.find_elements(By.XPATH,'//h1[contains(@class, "_ap3a")]')
		if desc_elements:description=desc_elements[0].text.strip().replace('\n','\\n')
		if not description:dbg(f'{DARK}[debug] description not found{RESET}')
	except Exception as e:print(f'{RED}[error] description: {e}{RESET}')
	try:
		time_elements=d.find_elements(By.XPATH,'//time[@class="x1p4m5qa"]')
		if time_elements:date_iso=time_elements[0].get_attribute('datetime')
		if not date_iso:dbg(f'{DARK}[debug] date not found{RESET}')
	except Exception as e:print(f'{RED}[error] date: {e}{RESET}')
	return description,date_iso

def click_next(d):	# click all carousel nexts btns, return click count
	clicks=0
	while True:
		try:
			nextbtn=d.find_element(By.XPATH,'//button[contains(@aria-label,"Next")]')
			if nextbtn.get_attribute('tabindex')=='-1':d.execute_script('arguments[0].click();',nextbtn);hsleep(0.5,1);clicks+=1
			else:break
		except:break
	return clicks

def click_post(d,element):
	try:
		if 'profile picture' in (element.find_element(By.TAG_NAME,'img').get_attribute('alt') or ''):return 'Profile picture',''	# dont click if pp + assigned desc
		d.execute_script('arguments[0].click();',element)
		hsleep(2,3)
		description,date_iso=get_desc_and_date(d)
		hsleep(1,3)
		d.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)
		hsleep(1,2)
		return description,date_iso
	except Exception as e:
		dbg(f'{DARK}[debug] modal click error: {e}{RESET}')
		try:d.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)
		except:pass
		return '',''

def tmp(url,name,tmpdir):	# fetch chunk to temp dir
	try:out=tmpdir/name;ffout(ffin(url,headers='Referer: https://www.instagram.com/'),str(out),vcodec='copy',acodec='copy').run(overwrite_output=True,quiet=True);return out
	except Exception as e:
		dbg(f'{DARK}[debug] chunk failed: {url} as {name} ({e}){RESET}')
		return None

def typ(f):	# audio / video?
	try:
		for s in ffprobe(str(f))['streams']:
			if s['codec_type']=='video':return'v'
			if s['codec_type']=='audio':return'a'
	except:return None

def save_pic(url,out,seen):
	k=media_key(url)
	if k in seen:return None,None
	for attempt in range(3):
		try:
			r=get(url,headers={'Referer':'https://www.instagram.com/'},timeout=10,proxies=PROXIES or None)
			if r.status_code==200:
				open(out,'wb').write(r.content)
				seen.add(k)
				dbg(f'{DARK}[debug] pic downloaded: {url}{RESET}')
				return out,k
		except Exception as e:
			dbg(f'{DARK}[debug] pic error (attempt {attempt+1}): {e}{RESET}')
		hsleep(2,3)
	print(f'{RED}[error] pic download failed: {url}{RESET}')
	return None,None

def save_vid(urls,folder,filename,seen):	# merge A+V
	if len(urls)<1:return None,[]
	makedirs(folder,exist_ok=True)
	keys=[]
	if len(urls)==1:
		u=urls[0]
		k=media_key(u)
		if k in seen:return None,[]
		out=join(folder,filename)
		try:
			r=get(u,headers={'Referer':'https://www.instagram.com/'},timeout=15,proxies=PROXIES or None)
			if r.status_code==200:
				open(out,'wb').write(r.content)
				seen.add(k)
				if is_video(out):
					dbg(f'{DARK}[debug] single video downloaded: {u}{RESET}')
					return out,[k]
		except Exception as e:
			print(f'{RED}[error] single video failed: {u} ({e}){RESET}')
		return None,[]
	with TemporaryDirectory()as t:
		tmpdir=Path(t);u=[clean(x)for x in urls];i=-2;af=None;vf=None;last_v=None
		while abs(i)<=len(u):
			af=tmp(u[i],'a.mp4',tmpdir)
			vf=tmp(u[i+1],'v.mp4',tmpdir)
			dbg(f'{DARK}[debug] trying: {u[i+1]} (v) / {u[i]} (a){RESET}')
			if af and vf:
				taf,tvf=typ(af),typ(vf)
				dbg(f'{DARK}[debug] types detected: {af}={taf}, {vf}={tvf}{RESET}')
				if (taf=='a' and tvf=='v') or (taf=='v' and tvf=='a'):
					out=join(folder,filename)
					try:
						if taf=='a' and tvf=='v':
							audio_file,video_file=str(af),str(vf)
						else:	# taf=='v' and tvf=='a'
							audio_file,video_file=str(vf),str(af)
						ffout(ffin(video_file),ffin(audio_file),out,vcodec='copy',acodec='aac',strict='experimental').run(overwrite_output=True,quiet=True)
						k1=media_key(u[i]);k2=media_key(u[i+1])
						keys.extend([k1,k2]);seen.add(k1);seen.add(k2)
						if is_video(out):
							dbg(f'{DARK}[debug] video merge successful: {filename}{RESET}')
							return out,keys
					except Exception as e:
						print(f'{RED}[error] merge failed: {video_file} + {audio_file} ({e}){RESET}')
						break
			if vf and typ(vf)=='v':
				last_v=vf;last_vk=media_key(u[i+1])
				dbg(f'{DARK}[debug] keeping video-only file: {vf}{RESET}')
			elif af and typ(af)=='v':
				last_v=af;last_vk=media_key(u[i])
				dbg(f'{DARK}[debug] keeping video-only file: {af}{RESET}')
			i-=1
		if last_v and exists(last_v) and getsize(last_v)>16*1024:
			out=join(folder,filename)
			open(out,'wb').write(open(last_v,'rb').read())
			seen.add(last_vk)
			if is_video(out):
				dbg(f'{DARK}[debug] video only downloaded: {out}{RESET}')
				return out,[last_vk]
	return None,[]

def scrape_netlogs(d,url,pics_folder,vid_folder,post_idx,seen,is_carousel=False,is_clip=False,is_pinned=False):
	global VID_COUNTER
	main_window=d.current_window_handle
	handles_before=set(d.window_handles)
	try:
		d.execute_script(f'window.open("{url}","_blank");');hsleep(1.5,2.7)
		handles_after=set(d.window_handles)
		new_tabs=list(handles_after-handles_before)
		d.switch_to.window(new_tabs[0])
		d.get_log('performance');hsleep(6,9);clicks=0
		if is_carousel or is_pinned:clicks=click_next(d);hsleep(1,1.6)
		description,date_iso=get_desc_and_date(d)
		if is_pinned and not description.strip():return [],[],[],'','','pin_no_desc'
		if is_pinned and clicks==0 and description.strip():return [],[],[],'','','single_photo'
		vid_keys_batch=set()
		pics,vids=[],[]
		for l in d.get_log('performance'):
			try:
				m=loads(l['message'])['message']
				if m['method']=='Network.responseReceived':
					u=m['params']['response']['url']
					k=media_key(u)
					if not is_clip and (('.jpg'in u or'.jpeg'in u) and not is_pp(u)):
						if k not in seen:pics.append(u)
					if('.mp4'in u):
						if k not in seen and k not in vid_keys_batch:vids.append(u);vid_keys_batch.add(k)
			except:continue
		pic_paths=[];media_keys=[];pic_count=1
		vid_paths=[]
		for pic_url in pics:
			pth,k=save_pic(pic_url,abspath(join(pics_folder,f'{post_idx}_{pic_count}.jpg')),seen)
			if pth:pic_paths.append(abspath(pth));media_keys.append(k);pic_count+=1
		if vids:
			fn=f'{post_idx}_{VID_COUNTER}.mp4' if is_carousel or is_pinned else f'{post_idx}.mp4'
			out,keys=save_vid(vids,vid_folder,fn,seen)
			if out and is_video(out):
				vid_paths.append(abspath(out))
				media_keys.extend(keys)
				if is_carousel or is_pinned:VID_COUNTER+=1
		return pic_paths,vid_paths,media_keys,description,date_iso,True
	except Exception as e:print(f'{RED}[error] scrape_netlogs: {e}{RESET}');return [],[],[],'','',False
	finally:
		try:d.switch_to.window(new_tabs[0])
		except:pass
		try:d.close()
		except:pass
		try:d.switch_to.window(main_window)
		except:pass
		hsleep(1,2)

def print_post(post):
	pics=[pic.get('path') for pic in post.get('pics',[]) if pic.get('path')]
	vids=[vid.get('path') for vid in post.get('vids',[]) if vid.get('path')]
	if post.get('is_clip'):post_type='video'
	if post.get('is_clip'):post_type='video'
	elif post.get('is_pinned'):post_type='pinned'
	elif post.get('is_carousel'):post_type='carousel'
	else:post_type='picture'
	date_str=post.get('date','') if post.get('date') else 'no date'
	description=post.get('description','').replace('\\n',' \\n ')
	msg=f'{PINK}[post {post.get("post_idx")}]{RESET} href: {post.get("href")}'
	if pics:msg+=f' - pics output: {",".join(pics)}'
	if vids:msg+=f' - vids output: {",".join(vids)}'
	if description and DBG:msg+=f'{DARK} - type: {post_type} - datetime: {date_str} - description: {description}{RESET}'
	print(msg)

def profile_loop(d,user,base,media_json_path):
	global VID_COUNTER
	try:
		pics_dir,vids_dir=join(base,'pics'),join(base,'vids')
		makedirs(pics_dir,exist_ok=True);makedirs(vids_dir,exist_ok=True)
		jsondata=load_json(media_json_path)
		post_idx=get_idx(jsondata)
		hrefs=get_hrefs(jsondata)
		seen=get_seen(jsondata)
		batch_count=0
		stale_counter=0
		total_found_hrefs=set()
		while True:
			try:
				posts=get_info(d,user)
				found_hrefs=set(a['href'] for a in posts if a['href'])
				if found_hrefs==total_found_hrefs:stale_counter+=1
				else:stale_counter=0
				total_found_hrefs=found_hrefs.copy()
				if stale_counter>=3 or not found_hrefs:break
				for info in posts:
					href=info['href']
					if not href or href in hrefs:continue
					VID_COUNTER=1
					post={'post_idx':post_idx,'href':href,'is_clip':info['is_clip'],'is_carousel':info['is_carousel'],'is_pinned':info['is_pinned'],'date':'','pics':[],'vids':[],'description':''}
					pic_paths,vid_paths,media_keys,description,date_iso=[],[],[],'','';processed_successfully=False
					if info['is_pinned']:
						pic_paths,vid_paths,media_keys,description,date_iso,success=scrape_netlogs(d,href,pics_dir,vids_dir,post_idx,seen,True,False,True)
						if success=='pin_no_desc' or success=='single_photo':
							reason='without description' if success=='pin_no_desc' else 'with single photo'
							dbg(f'{DARK}[debug] pin {reason}, processing as single picture{RESET}')
							if info['pic']:
								k=media_key(info['pic'])
								if k not in seen:
									description,date_iso=click_post(d,info['element'])
									pic_path,key=save_pic(info['pic'],abspath(join(pics_dir,f'{post_idx}.jpg')), seen)
									if pic_path and description:
										post['pics']=[{'url':info['pic'],'path':abspath(pic_path),'media_key':key}]
										processed_successfully=True
						else:
							dbg(f'{DARK}[debug] pin processed as carousel{RESET}')
							post['pics']=[{'url':'','path':p,'media_key':k}for p,k in zip(pic_paths,media_keys[:len(pic_paths)])]
							post['vids']=[{'url':'','path':p,'media_key':k}for p,k in zip(vid_paths,media_keys[len(pic_paths):])]
							processed_successfully=success and (pic_paths or vid_paths)
					elif info['is_carousel']:
						pic_paths,vid_paths,media_keys,description,date_iso,success=scrape_netlogs(d,href,pics_dir,vids_dir,post_idx,seen,True,False,False)
						if success=='single_photo':
							dbg(f'{DARK}[debug] carousel with single photo, processing as single picture{RESET}')
							if info['pic']:
								k=media_key(info['pic'])
								if k not in seen:
									description,date_iso=click_post(d,info['element'])
									pic_path,key=save_pic(info['pic'],abspath(join(pics_dir,f'{post_idx}.jpg')), seen)
									if pic_path and description:
										post['pics']=[{'url':info['pic'],'path':abspath(pic_path),'media_key':key}]
										processed_successfully=True
						else:
							post['pics']=[{'url':'','path':p,'media_key':k}for p,k in zip(pic_paths,media_keys[:len(pic_paths)])]
							post['vids']=[{'url':'','path':p,'media_key':k}for p,k in zip(vid_paths,media_keys[len(pic_paths):])]
							processed_successfully=success and (pic_paths or vid_paths)
					elif info['is_clip']:
						pic_paths,vid_paths,media_keys,description,date_iso,success=scrape_netlogs(d,href,pics_dir,vids_dir,post_idx,seen,False,True,False)
						post['vids']=[{'url':'','path':p,'media_key':k}for p,k in zip(vid_paths,media_keys)]
						processed_successfully=success and vid_paths
					elif info['pic']:
						k=media_key(info['pic'])
						if k not in seen:
							description,date_iso=click_post(d,info['element'])
							pic_path,key=save_pic(info['pic'],abspath(join(pics_dir,f'{post_idx}.jpg')),seen)
							if pic_path:
								post['pics'].append({'url':info['pic'],'path':abspath(pic_path),'media_key':key})
								processed_successfully=True
					post['date']=date_iso;post['description']=description;should_save=False
					if processed_successfully and description:
						if (not info['is_clip'] and not info['is_carousel'] and not info['is_pinned']) or (info['is_clip'] and any(is_video(v.get('path')) for v in post['vids'])) or ((info['is_carousel'] or info['is_pinned']) and (all(is_video(v.get('path')) for v in post['vids']) if post['vids'] else True)):
							if post['pics'] or post['vids']:should_save=True
					if should_save:
						print_post(post)
						jsondata.append(post)
						save_json(media_json_path,jsondata)
						post_idx+=1;batch_count+=1
						hrefs.add(href)
						if batch_count%BATCH==0:
							d.refresh();hsleep(5,7)
				d.execute_script(f'window.scrollBy(0,{randint(800,1600)});');hsleep(1.2,2.7);d.get_log('performance')
			except Exception as e:print(f'{RED}[error] profile_loop iteration: {e}{RESET}');continue
	except Exception as e:print(f'{RED}[error] profile_loop: {e}{RESET}');return

def main():
	global PROXIES,DBG,PROXY_ARGS,a
	ap=ArgumentParser(description='ig profile media downloader')
	ap.add_argument('--profile_url',required=True,help='instagram profile url')
	ap.add_argument('--cookies',help='path to cookies json file')
	ap.add_argument('--proxy',help='proxy url')
	ap.add_argument('--output',help='custom path directory for results')
	ap.add_argument('--debug',action='store_true',help='enable debug mode')
	a=ap.parse_args()
	DBG=a.debug
	if a.proxy:
		try:
			parsed=urlparse(a.proxy)
			if parsed.hostname and parsed.port:
				if parsed.scheme=='socks5':
					proxy_url=f'socks5://{parsed.hostname}:{parsed.port}'
					PROXIES={'http':proxy_url,'https':proxy_url}
					PROXY_ARGS=['-http_proxy',proxy_url]
					dbg(f'{DARK}[debug] socks5 proxy configured for requests{RESET}')
				else:
					if parsed.username and parsed.password:proxy_url=f'http://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}'
					else:proxy_url=f'http://{parsed.hostname}:{parsed.port}'
					PROXIES={'http':proxy_url,'https':proxy_url}
					PROXY_ARGS=['-http_proxy',proxy_url]
					dbg(f'{DARK}[debug] http proxy configured for requests{RESET}')
		except Exception as e:print(f'{RED}[error] proxy config: {e}{RESET}')
	user=uname(a.profile_url)
	base=abspath(a.output)if a.output else abspath(join('results',user))
	media_json_path=join(base,'data.json')
	dbg(f'{DARK}[debug] starting scraper for user: {user}{RESET}')
	while True:
		try:
			dbg(f'{DARK}[debug] creating driver with proxy...{RESET}')
			d=drv((a.proxy if a.proxy else None))
			try:
				if DBG:dbg_stealth(d)
				if a.cookies and (cookies:=load_cookies(d, a.cookies)):
					dbg(f'{DARK}[debug] refreshing page...{RESET}')
					d.refresh();hsleep(3,5)
				verify_login(d)
				dbg(f'{DARK}[debug] navigating to profile {a.profile_url}{RESET}')
				d.get(a.profile_url);hsleep(3, 5)
				current_title=d.title
				dbg(f'{DARK}[debug] page title: {current_title}{RESET}')
				dbg(f'{DARK}[debug] starting profile scraping...{RESET}')
				profile_loop(d,user,base,media_json_path)
			finally:
				try:
					d.quit()
					dbg(f'{DARK}[debug] driver closed{RESET}')
				except:pass
			break
		except Exception as e:print(f'{RED}[error] main loop: {e}{RESET}');sleep(10)

if __name__=='__main__':main()
	# by azuk4r
	# ¬_¬
