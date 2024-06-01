#!/usr/bin/python3
import sys
import re

args = sys.argv

if len(args) < 2 or args[1] == '' or args[2] == '':
	print('Usage: fontjis2ucs [-j][-s] <bdf file> ([-j][-s] <bdf file> ...) <outputfile>')
	sys.exit(1)

# ヘッダ関連
re_pixelsize = re.compile(r'PIXEL_SIZE\s+(\d+)')
re_fontascent = re.compile(r'FONT_ASCENT\s+(\d+)')
re_chars = re.compile(r'^CHARS\s+(\d+)')

re_startfont = re.compile(r'^STARTFONT')
re_endfont = re.compile(r'^ENDFONT')

# フォント文字毎
re_startchar = re.compile(r'^STARTCHAR')
re_encoding = re.compile(r'^ENCODING\s+(\d+)')
re_endchar = re.compile(r'^ENDCHAR')

def readbdf(bdf):
	font = {
		'pixelsize': None,
		'fontascent': None,
		'chars': None,
		'startfont': None,
		'data': None,
	}
	fontdata = []

	def chara_init():
		return {
			'startchar': None,
			'encoding': None,
			'data': None,
		}
	chara = chara_init()
	cdata = []

	with open(bdf, 'r') as infp:
		for l in infp.readlines():
			l = l.rstrip()
			if font['chars'] is None:
				# ヘッダまだ
				if font['pixelsize'] is None and re_pixelsize.match(l):
					font['pixelsize'] = l
				elif font['fontascent'] is None and re_fontascent.match(l):
					font['fontascent'] = l
				elif font['chars'] is None and (r := re_chars.match(l)):
					font['chars'] = int(r.group(1))
				elif re_startfont.match(l):
					font['startfont'] = l
			else:
				if chara['startchar']:
					if (r := re_encoding.match(l)):
						chara['encoding'] = int(r.group(1))
					elif re_endchar.match(l):
						chara['data'] = cdata
						fontdata.append(chara)
						chara = chara_init()
						cdata = []
					else:
						cdata.append(l)
				elif re_startchar.match(l):
					chara['startchar'] = l
		
		if font['chars'] != len(fontdata):
			print("Wmm ... %s: CHARAS %d / %d" % (bdf, font['chars'], len(fontdata)))
		
		font['data'] = fontdata

	return font


# フォントごとの出力
def char_put(cd, fp):
	print(cd['startchar'], file=fp)
	print("ENCODING %d" % (cd['encoding']), file=fp)
	for l in cd['data']:
		print(l, file=fp)
	print("ENDCHAR", file=fp)


# コードの変換
# jis0208 -> utf16
def jis2utf16le(bdf):
	for c in bdf['data']:
		ucs = c['encoding']
		unicode = int.from_bytes((b'\x1b$B' + ucs.to_bytes(2, 'big')).decode('iso2022jp').encode('utf_16_be'), byteorder='big')
		c['encoding'] = unicode

# ascii -> 0xff00～ (半角カナ)
def ascii2utf16_0xff00(bdf):
	for c in bdf['data']:
		ucs = c['encoding']
		if ucs < 0x7f:
			# 20 -> FF00
			ucs += 0xff00 - 0x20
		else:
			# a1 -> FF61
			ucs += 0xff61 - 0xa1
		if ucs < 0xff00 or ucs > 0xffff:
			ucs = 0xffff
		c['encoding'] = ucs

# コードの変換(c1 -> c2)
# c2 < 0: 削除
def remap_code(bdf, c1, c2):
	d = c2
	if d < 0:
		d = c1
	for i in range(len(bdf['data'])):
		c = bdf['data'][i]
		if c is None:
			continue
		elif c['encoding'] == d:
			bdf['data'][i] = None
		elif c['encoding'] == c1:
			c['encoding'] = c2


#
# メイン処理
#
fonts = []
flags = ''

for opt in args[1:-1]:
	if r := re.match(r'^-([jh]+)', opt):
		flags += r.group(1)
	else:
		bdf = opt
		f = {}
		f['flags'] = flags
		f['bdf'] = readbdf(bdf)
		fonts.append(f)
		flags = ''

# コードの変換
# j : jis -> utf-16-be
# h : 半角 -> 0xff00 - 0xffff に割り当て 
for bdf in fonts:
	if bdf['flags'] == 'j':
		jis2utf16le(bdf['bdf'])
	elif bdf['flags'] == 'h':
		ascii2utf16_0xff00(bdf['bdf'])

# remap	(WindowsのUnicode変換マップ)
# ∥
remap_code(fonts[0]['bdf'], 8214, 8741)
# ～
remap_code(fonts[0]['bdf'], 12316, 65374)
remap_code(fonts[1]['bdf'], 65374, -1)
# －
remap_code(fonts[0]['bdf'], 8722, 65293)
remap_code(fonts[1]['bdf'], 65293, -1)
# ―
remap_code(fonts[0]['bdf'], 8212, 8213)

# conio.c で 0x30fc -> 0x2014 に変更されている
# 「ゲーム」の文字化けが修正される
remap_code(fonts[0]['bdf'], 0x30fc, 0x2014)

# コード重複などの処理
chars = 0
codetab = [ None for i in range(0x10000) ]
for bdf in fonts:
	for cd in bdf['bdf']['data']:
		if cd is None:
			continue
		elif codetab[cd['encoding']] is None:
			chars += 1
		codetab[cd['encoding']] = cd

outfp = open(args[-1], 'w')

top = fonts[0]['bdf']
print(top['startfont'], file=outfp)
print(top['pixelsize'], file=outfp)
print(top['fontascent'], file=outfp)

print("CHARS %d" % (chars), file=outfp)

for fd in codetab:
	if fd:
		char_put(fd, outfp)

print("ENDFONT", file=outfp)
