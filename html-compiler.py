__author__ = 'El1t'
from html.parser import HTMLParser
from base64 import b64encode
from urllib.request import urlopen
from os.path import exists, isfile
from re import split
from sys import argv

extensions = {
	'.css' : 'text/css',
	'.jpg' : 'image/jpeg',
	'.jpeg': 'image/jpeg',
	'.js'  : 'text/javascript',
	'.png' : 'image/png',
}


def css(output, path, attrs):
	output.write('<style>')
	for attr in attrs:
		if attr[0] == 'href':
			print('Inserting css file:', path + attr[1])
			with open(path + attr[1], 'r') as read:
				output.write(read.read())
	output.write('</style>')


def js(output, path, attrs):
	read = None
	output.write('<script')
	for attr in attrs:
		if attr[0] == 'src':
			print('Inserting javascript file:', path + attr[1])
			read = open(path + attr[1], 'r')
		else:
			output.write(' ' + attr[0] + '="' + ' '.join(attr[1:]) + '"')
	output.write('>')
	output.write(read.read())
	read.close()
	output.write('</script>')


# def image(output, path, attrs):
# 	output.write('<img')
# 	for attr in attrs:
# 		if attr[0] == 'src':
# 			encode('src', attr[1], output, path)
# 		else:
# 			output.write(' ' + attr[0] + '="' + ' '.join(attr[1:]) + '"')
# 	output.write(' />')


def encode(path, output, local_path, attr=True):
	if attr:
		output.write('data:')
	if not isfile(path) and path[0] != '/' and isfile(local_path + path):
		# Prepend local path
		path = local_path + path
	if isfile(path):
		print('Encoding local file:', path)
		# Use local path
		with open(path, 'r') as read:
			output.write(extensions[path[path.rindex('.'):]] + ';base64,' + str(b64encode(read.read()), 'utf-8'))
	else:
		# Try remote path
		print('Encoding remote file:', path)
		output.write(extensions[path[path.rindex('.'):]] + ';base64,' + str(b64encode(urlopen(path).read()), 'utf-8'))


def style(styles, output, local_path):
	styles = split('url\(', styles)
	output.write(styles[0])
	if len(styles) > 1:
		for style in styles[1:]:
			output.write('url(data:')
			encode(style[1:style.index(')') - 1], output, local_path, False)
			output.write(style[style.index(')'):])


handles = {
	'link'  : css,
	'script': js,
	# 'img'   : image
}

handleAttribs = {
	'src'  : encode,
	'style': style
}


class Parser(HTMLParser):
	def __init__(self, path, output):
		super(Parser, self).__init__()
		self.path = path
		self.output = output
		self.skipNextEndTag = False

	def handle_starttag(self, tag, attrs):
		if tag in handles:
			handles[tag](self.output, self.path, attrs)
			self.skipNextEndTag = True
		else:
			self.output.write('<' + tag)
			for attr in attrs:
				self.output.write(' ' + attr[0] + '="')
				if attr[0] in handleAttribs:
					handleAttribs[attr[0]](attr[1], self.output, self.path)
				else:
					self.output.write(' '.join(attr[1:]))
				self.output.write('"')
			self.output.write('>')

	def handle_data(self, data):
		self.output.write(data)

	def handle_endtag(self, tag):
		if not self.skipNextEndTag:
			self.output.write('</' + tag + '>')
		self.skipNextEndTag = False


def main():
	i = 0
	for i, s in enumerate(argv[1][::-1]):
		if s == '/':
			break
	if not isfile(argv[1]):
		print('File not found')
		return
	with open(argv[1][:i] + 'output.html', 'w') as output:
		p = Parser(argv[1][:i], output)
		p.feed(open(argv[1], 'r').read())

if __name__ == '__main__':
	main()