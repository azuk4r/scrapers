from selenium.common.exceptions import StaleElementReferenceException,ElementClickInterceptedException,NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from os.path import join,exists,abspath,dirname,isfile
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.common.by import By
from argparse import ArgumentParser
from urllib.parse import urlparse
from os import makedirs,remove
from ffmpeg import input,Error
from time import sleep,time
from re import compile,sub
from requests import get
from json import loads

CH_BRANDS=[{'brand':'Not)A;Brand','version':'8'},{'brand':'Chromium','version':'138'},{'brand':'Google Chrome','version':'138'}]
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
DARK='\033[38;2;140;140;140m';RED='\033[38;2;168;0;0m';RESET='\033[0m'
W,H=1920,1080
PROXIES={}

parser=ArgumentParser(description='pinterest pins downloader by keywords')
parser.add_argument('keywords',type=str,nargs='?',help='keywords to download content (can use "keywords.txt" with a list)')
parser.add_argument('--proxy',help='proxy url')
parser.add_argument('--debug',action='store_true',help='enable debug mode')
args=parser.parse_args()
processed_images=set()
downloaded_media=set()
driver_service=None
media_groups={}

def dbg(t): print(f'{DARK}{t}{RESET}') if args.debug else None
def scroll_down(driver): driver.execute_script('window.scrollBy(0,100);');sleep(.5)
def extract_unique_id(url): uid_match=compile(r'/([a-f0-9]{32})').search(url);return uid_match.group(1) if uid_match else None

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
					dbg(f'[debug] proxy: {parsed.hostname}:{parsed.port}{RESET}')
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
		dbg(f'[debug] stealth check started')
		for url in urls:
			try:
				dbg(f'[debug] {url.split("/")[-1]}...')
				d.get(url)
				sleep(5)
				if 'webrtc' in url:
					try:
						ipv4_element=d.find_element(By.ID,'client-ipv4')
						ip=ipv4_element.get_attribute('data-ip')
						country=ipv4_element.get_attribute('data-iso_code')
						dbg(f'[debug] ip: {ip} ({country})')
						leak_element=d.find_element(By.ID,'rtc-leak')
						status='no leak' if 'No Leak' in leak_element.text else 'leak'
						dbg(f'[debug] webrtc: {status}')
					except Exception as e:
						dbg(f'[debug] webrtc: failed')
				elif 'javascript' in url:
					try:
						try:d.find_element(By.CLASS_NAME,'more-button').click();sleep(2)
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
						dbg(f'[debug] platform: {platform.lower()}')
						wd_status="hidden" if webdriver=="undefined" else "detected"
						dbg(f'[debug] webdriver: {wd_status}')
						dbg(f'[debug] plugins: {plugins[:50]}...')
						dbg(f'[debug] mimeTypes: {mimetypes[:50]}...')
						dbg(f'[debug] deviceMemory: {device_memory}')
						dbg(f'[debug] language: {language}')
						dbg(f'[debug] languages: {languages}')
						dbg(f'[debug] vendor: {vendor}')
						dbg(f'[debug] hardwareConcurrency: {hardware}')
						dbg(f'[debug] screen: {width}x{height} ({avail_width}x{avail_height})')
						dbg(f'[debug] colorDepth: {color_depth}, pixelDepth: {pixel_depth}')
						dbg(f'[debug] orientation: {orientation}')
					except Exception as e:dbg(f'[debug] javascript: failed')
				elif 'canvas' in url:
					try:
						sig_element=d.find_element(By.ID,'canvas-hash')
						uniqueness_element=d.find_element(By.ID,'canvas-ratio')
						signature=sig_element.text.strip()
						uniqueness=uniqueness_element.text.strip()
						dbg(f'[debug] canvas: {signature}')
						dbg(f'[debug] canvas uniqueness: {uniqueness}')
					except Exception as e:dbg(f'[debug] canvas: failed')
				elif 'webgl' in url:
					try:
						report_hash_element=d.find_element(By.ID,'gl-report-hash')
						webgl_report_hash=report_hash_element.text.strip()
						dbg(f'[debug] webgl report hash: {webgl_report_hash}')
						image_hash_element=d.find_element(By.ID,'gl-image-hash')
						webgl_image_hash=image_hash_element.text.strip()
						dbg(f'[debug] webgl image hash: {webgl_image_hash}')
						vendor_element=d.find_element(By.ID,'UNMASKED_VENDOR_WEBGL')
						renderer_element=d.find_element(By.ID,'UNMASKED_RENDERER_WEBGL')
						vendor=sub(r'!\s*','',vendor_element.text).strip()
						renderer=sub(r'!\s*','',renderer_element.text).strip()
						dbg(f'[debug] webgl vendor: {vendor}')
						dbg(f'[debug] webgl renderer: {renderer}')
					except Exception as e:dbg(f'[debug] webgl: failed')
				sleep(4)
			except Exception as e:
				dbg(f'[debug] {url.split("/")[-1]}: failed')
				continue
		dbg(f'[debug] stealth check completed')
		return True
	except Exception as e:
		dbg(f'[debug] stealth check: error')
		return False

def download_image(img_url,folder,name):
	if not img_url.startswith('http') or img_url.endswith('.svg'):return False
	for size in ['originals','736x','474x']:
		adjusted_url=img_url.replace('/236x/',f'/{size}/').replace('/474x/',f'/{size}/').replace('/736x/',f'/{size}/')
		response=get(adjusted_url,proxies=PROXIES or None)
		if response.status_code==200:
			img_path=join(folder,name)
			with open(img_path,'wb') as file:file.write(response.content)
			print(f'{RED}[pindownloader]{RESET} image: {name}')
			return True
	return False

def download_video_or_audio(url,folder,name,kind):
	try:
		response=get(url,stream=True,proxies=PROXIES or None)
		if response.status_code==200:
			path=join(folder,name)
			with open(path,'wb') as f:
				for chunk in response.iter_content(1024*1024):f.write(chunk)
			print(f'{RED}[pindownloader]{RESET} {kind}: {name}')
			return path
	except Exception:pass
	return None

def close_popup(driver):
	while True:
		try:
			popup=driver.find_element(By.CSS_SELECTOR,'div.MIw.QLY.Rz6.hDW.p6V.zI7.iyn.Hsu')
			driver.execute_script('arguments[0].scrollIntoView(true);',popup)
			sleep(.1)
			popup.click()
		except NoSuchElementException:break
		except ElementClickInterceptedException:sleep(.1)

def merge_video(output_folder,media_id,media_data):
	video_url=media_data.get('video')
	audio_url=media_data.get('audio')
	if video_url and audio_url:
		video_file=join(output_folder,f'tmp_video_{media_id}.mp4')
		audio_file=join(output_folder,f'tmp_audio_{media_id}.mp4')
		output_file=join(output_folder,f'video_{media_id}.mp4')
		video_path=download_video_or_audio(video_url,output_folder,f'tmp_video_{media_id}.mp4','video')
		audio_path=download_video_or_audio(audio_url,output_folder,f'tmp_audio_{media_id}.mp4','audio')
		if not video_path or not audio_path:
			if video_path and exists(video_path):remove(video_path)
			if audio_path and exists(audio_path):remove(audio_path)
			return
		try:
			in_video=input(video_file)
			in_audio=input(audio_file)
			(in_video.output(in_audio,output_file,c='copy').overwrite_output().run(quiet=True))
			remove(video_file)
			remove(audio_file)
			print(f'{RED}[pindownloader]{RESET} merge: {output_file}')
		except Error:
			if exists(video_file):remove(video_file)
			if exists(audio_file):remove(audio_file)
	elif video_url and not audio_url:download_video_or_audio(video_url,output_folder,f'video_{media_id}_noaudio.mp4','video (no audio)')
	elif audio_url and not video_url:pass

def process_element(element,driver,actions,output_folder):
	global last_mouseover_time
	try:
		if element.size['width']<=60 or element.size['height']<=60:return
		src=element.get_attribute('poster') or element.get_attribute('src')
		image_id=extract_unique_id(src)
		if image_id in processed_images:return
		processed_images.add(image_id)
		driver.execute_script('arguments[0].scrollIntoView({block: "center"});',element)
		sleep(.1)
		actions.move_to_element(element).perform()
		sleep(.3)
		last_mouseover_time=time()
		image_name=f'img_{image_id}.jpg'
		if not download_image(src,output_folder,image_name):return
		logs=driver.get_log('performance')
		video_audio_pairs={}
		for log in logs:
			log_str=str(log)
			if '.cmfv' in log_str or '.cmfa' in log_str:
				try:
					log_json=loads(log['message'])
					cmfx_url=log_json['message']['params']['request']['url']
					if cmfx_url in downloaded_media:continue
					media_id=extract_unique_id(cmfx_url)
					if media_id not in video_audio_pairs:video_audio_pairs[media_id]={'video':None,'audio':None,'image_id':image_id}
					if '_audio.cmfa' in cmfx_url:video_audio_pairs[media_id]['audio']=cmfx_url
					elif any(res in cmfx_url for res in ['_360w.cmfv','_240w.cmfv']):
						current_video=video_audio_pairs[media_id]['video']
						if not current_video or('_240w.cmfv' in current_video and '_360w.cmfv' in cmfx_url):video_audio_pairs[media_id]['video']=cmfx_url
					downloaded_media.add(cmfx_url)
				except(KeyError,ValueError):continue
		for media_id,media_data in video_audio_pairs.items():
			if media_id not in media_groups:
				media_groups[media_id]=media_data
				merge_video(output_folder,media_id,media_data)
	except StaleElementReferenceException:scroll_down(driver)
	except Exception:
		close_popup(driver)
		scroll_down(driver)

def main():
	global driver_service,last_mouseover_time,media_groups,processed_images,downloaded_media,PROXIES
	if args.proxy:
		try:
			parsed=urlparse(args.proxy)
			if parsed.hostname and parsed.port:
				if parsed.scheme=='socks5':
					proxy_url=f'socks5://{parsed.hostname}:{parsed.port}'
					PROXIES={'http':proxy_url,'https':proxy_url}
					dbg('[debug] socks5 proxy configured for requests')
				else:
					if parsed.username and parsed.password:proxy_url=f'http://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}'
					else:proxy_url=f'http://{parsed.hostname}:{parsed.port}'
					PROXIES={'http':proxy_url,'https':proxy_url}
					dbg('[debug] http proxy configured for requests')
		except Exception as e:print(f'{RED}[error] proxy config: {e}{RESET}')
	keywords=[args.keywords] if args.keywords else[]
	if not keywords and isfile('keywords.txt'):
		with open('keywords.txt') as f:keywords=[line.strip() for line in f if line.strip()]
	if not keywords:
		print(f'{RED}[pindownloader]{RESET} no keywords found. use the argument or "keywords.txt"')
		return
	for query in keywords:
		processed_images=set()
		media_groups={}
		downloaded_media=set()
		encoded_query=query.replace(' ','%20')
		url=f'https://es.pinterest.com/search/pins/?q={encoded_query}&rs=typed'
		driver=drv(args.proxy)
		if args.debug:dbg_stealth(driver)
		driver.get(url)
		sleep(3)
		actions=ActionChains(driver)
		current_dir=dirname(abspath(__file__))
		output_folder=join(current_dir,query)
		if not exists(output_folder):makedirs(output_folder)
		last_mouseover_time=time()
		while True:
			if time()-last_mouseover_time>60:break
			try:
				elements=driver.find_elements(By.CSS_SELECTOR,'img.hCL')
				if not elements:scroll_down(driver)
				else:
					for element in elements:process_element(element,driver,actions,output_folder)
			except Exception:
				close_popup(driver)
				scroll_down(driver)
		driver.quit()

if __name__=='__main__':main()
	# by azuk4r
	# ¬_¬
