__author__ = 'El1t'
from html.parser import HTMLParser
from base64 import b64encode
from urllib.request import urlopen
from os.path import exists, isfile
from re import split
from sys import argv


class Parser(HTMLParser):
	extensions = {
		# Multipurpose
		'.ogg' : 'application/ogg',
		'.pdf' : 'application/pdf',
		'.xml' : 'application/xml',
		# Text
		'.css' : 'text/css',
		'.js'  : 'text/javascript',
		# Images
		'.jpg' : 'image/jpeg',
		'.jpeg': 'image/jpeg',
		'.png' : 'image/png',
		'.gif' : 'image/gif',
		'.bmp' : 'image/bmp',
		'.tif' : 'image/tiff',
		# Audio
		'.au'  : 'audio/basic',
		'.flac': 'audio/flac',
		'.m4a' : 'audio/mp4',
		'.mpa': 'audio/mpeg',
		'.opus': 'audio/opus',
		# Video
		'.avi' : 'video/avi',
		'.m4v' : 'video/mp4',
		'.mov' : 'video/quicktime',
		'.mpv' : 'video/mpeg',
		'.ogv' : 'video/ogg'
	}
	handles = {
		'link'  : ['css', 'href'],
		'script': ['js',  'src']
	}

	def __init__(self, path, output):
		super(Parser, self).__init__()
		self.path = path
		self.output = output
		self.files = {
			'css': [],
			'js' : []
		}

	def handle_starttag(self, tag, attrs):
		if tag.lower() in self.handles:
			file_type, attribute = self.handles[tag.lower()]
			for attr in attrs:
				if attr[0].lower() == attribute:
					# Queue up file for outputting later
					self.files[file_type].append(attr[1])
		else:
			mime_extension, source = None, None
			self.output.write('<' + tag)
			for attr in attrs:
				if attr[0].lower() == 'style':
					self.output.write(' ' + attr[0] + '="')
					self.handle_style(attr[1])
					self.output.write('"')
				elif attr[0].lower() == 'type':
					mime_extension = attr[1]
				elif attr[0].lower() == 'src':
					source = attr[1]
				else:
					self.output.write(' ' + attr[0] + '="' + ' '.join(attr[1:]) + '"')
			if source:
				self.output.write(' src="data:')
				self.encode(self.resolve_path(source), mime_extension)
				self.output.write('"')
			self.output.write('>')

	def handle_data(self, data):
		self.output.write(data)

	def handle_endtag(self, tag):
		# Output file queues at end of head and body
		if tag.lower() == 'head':
			self.output_css()
			self.output_js()
		elif tag.lower() == 'body':
			self.output_js()
		self.output.write('</' + tag + '>')

	def handle_style(self, styles):
		styles = split('url\(', styles)
		self.output.write(styles[0])
		if len(styles) > 1:
			for style in styles[1:]:
				self.output.write('url(data:')
				print('Encoding file from', end=' ')
				self.encode(self.resolve_path(style[1:style.index(')') - 1]))
				self.output.write(style[style.index(')'):])

	def resolve_path(self, path):
		mime_extension = self.extensions[path[path.rindex('.'):]]
		if not isfile(path) and path[0] != '/' and isfile(self.path + path):
			# Prepend local path
			path = self.path + path
		print(path)
		if isfile(path):
			# Use local path
			with open(path, 'r') as read:
				return read.read(), mime_extension
		else:
			# Try remote path
			return urlopen(path).read(), mime_extension

	def output_css(self):
		self.output.write('<style>')
		for file_path in self.files['css']:
			print('Inserting css file from', end=' ')
			self.output.write(self.resolve_path(file_path)[0])
		self.output.write('</style>')
		self.files['css'] = []

	def output_js(self):
		self.output.write('<script type="text/javascript">')
		for file_path in self.files['js']:
			print('Inserting javascript file from', end=' ')
			self.output.write(self.resolve_path(file_path)[0])
		self.output.write('</script>')
		# Clear file queue for scripts in body of html
		self.files['js'] = []

	def encode(self, file, extension=None):
		if extension:
			contents = file[0]
		else:
			contents, extension = file
		self.output.write(extension + ';base64,' + str(b64encode(contents), 'utf-8'))


def main():
	file = argv[1]
	if not isfile(file):
		print('File not found')
		return
	index = file.rfind('/')
	path = file[:index + 1] if index > -1 else './'
	with open(path + 'output.html', 'w') as output:
		p = Parser(path, output)
		p.feed(open(file, 'r').read())

if __name__ == '__main__':
	main()