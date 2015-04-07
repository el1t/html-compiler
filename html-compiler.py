__author__ = 'El1t'
from html.parser import HTMLParser
from base64 import b64encode
from urllib.request import urlopen
from os.path import exists, isfile
from re import split
from sys import argv


class Parser(HTMLParser):
	def __init__(self, path, output):
		super(Parser, self).__init__()
		self.path = path
		self.output = output
		self.files = {
			'css': [],
			'js' : []
		}

	def handle_starttag(self, tag, attrs):
		if tag in self.handles:
			for attr in attrs:
				if attr[0] == self.handles[tag][1]:
					# Queue up file for outputting later
					self.files[self.handles[tag][0]].append(attr[1])
		else:
			self.output.write('<' + tag)
			for attr in attrs:
				self.output.write(' ' + attr[0] + '="')
				if attr[0] in self.handleAttribs:
					self.handleAttribs[attr[0]](self, attr[1])
				else:
					self.output.write(' '.join(attr[1:]))
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
				self.encode(self.resolve_path(style[1:style.index(')') - 1]), False)
				self.output.write(style[style.index(')'):])

	def resolve_path(self, path):
		extension = self.extensions[path[path.rindex('.'):]]
		if not isfile(path) and path[0] != '/' and isfile(self.path + path):
			# Prepend local path
			path = self.path + path
		print(path)
		if isfile(path):
			# Use local path
			with open(path, 'r') as read:
				return read.read(), extension
		else:
			# Try remote path
			return urlopen(path).read(), extension

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

	def encode(self, file, attr=True):
		contents, extension = file
		if attr:
			self.output.write('data:')
		self.output.write(extension + ';base64,' + str(b64encode(contents), 'utf-8'))

	# Static vars
	handleAttribs = {
		'src'  : encode,
		'style': handle_style
	}
	extensions = {
		'.css' : 'text/css',
		'.jpg' : 'image/jpeg',
		'.jpeg': 'image/jpeg',
		'.js'  : 'text/javascript',
		'.png' : 'image/png',
		}
	handles = {
		'link'  : ['css', 'href'],
		'script': ['js',  'src']
	}


def main():
	file = argv[1]
	index = file.rfind('/')
	path = file[:index + 1] if index > -1 else './'
	if not isfile(argv[1]):
		print('File not found')
		return
	with open(path + 'output.html', 'w') as output:
		p = Parser(path, output)
		p.feed(open(file, 'r').read())

if __name__ == '__main__':
	main()