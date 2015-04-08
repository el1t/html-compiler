__author__ = 'El1t'
from html.parser import HTMLParser
from base64 import b64encode
from urllib.request import urlopen
from os.path import isfile, relpath, join, dirname, splitext
from os import chdir, getcwd
from re import split, match
from sys import argv, exit
from rjsmin import jsmin
from rcssmin import cssmin


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
		'.mpa' : 'audio/mpeg',
		'.mp2' : 'audio/mpeg',
		'.mp3' : 'audio/mpeg',
		'.opus': 'audio/opus',
		'.mid' : 'audio/midi',
		'.midi': 'audio/midi',
		# Video
		'.avi' : 'video/avi',
		'.m4v' : 'video/mp4',
		'.mov' : 'video/quicktime',
		'.m1v' : 'video/mpeg',
		'.ogv' : 'video/ogg'
	}
	handles = {
		'link'  : ['css', 'href'],
		'script': ['js',  'src']
	}
	default_options = {
		'v': False,
		'm': False
	}

	def __init__(self, output, options=None):
		super(Parser, self).__init__()
		self.output = output
		self.files = {
			'css': [],
			'js' : []
		}
		self.options = options if options else self.default_options
		self.skip_end_tag = False

	def handle_starttag(self, tag, attrs):
		if tag.lower() in self.handles:
			file_type, attribute = self.handles[tag.lower()]
			for attr in attrs:
				if attr[0].lower() == attribute:
					# Queue up file for outputting later
					self.files[file_type].append(attr[1])
					self.skip_end_tag = True
					break
			else:
				# Not referencing an external file
				self.output.write('<' + tag)
				for attr in attrs:
					self.output.write(' ' + attr[0] + '="' + ' '.join(attr[1:]) + '"')
				self.output.write('>')
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
				file, extension = self.resolve_path(source)
				if not mime_extension:
					mime_extension = extension
				if self.options['v']:
					print('Encoding', dirname(mime_extension), 'from', source)
				self.encode(file, mime_extension)
				self.output.write('"')
			self.output.write('>')

	def handle_data(self, data):
		self.output.write(data)

	def handle_endtag(self, tag):
		# Output file queues at end of head and body
		tag = tag.lower()
		if tag == 'head':
			self.output_css()
			self.output_js()
		elif tag == 'body':
			self.output_js()
		elif self.skip_end_tag:
			self.skip_end_tag = False
		else:
			self.output.write('</' + tag + '>')

	def handle_style(self, styles):
		styles = split('url\(', styles)
		self.output.write(styles[0])
		if len(styles) > 1:
			for style in styles[1:]:
				self.output.write('url(data:')
				path = style[1:style.index(')') - 1]
				file, extension = self.resolve_path(path)
				if self.options['v']:
					print('Encoding', dirname(extension), 'from', path)
				self.encode(file, extension)
				self.output.write(style[style.index(')'):])

	def resolve_path(self, path):
		mime_extension = self.extensions[splitext(path)[1]]
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
			if self.options['v']:
				print('Inserting css from', file_path)
			if self.options['m']:
				self.output.write(cssmin(self.resolve_path(file_path)[0]))
			else:
				self.output.write(self.resolve_path(file_path)[0])
		self.output.write('</style>')
		self.files['css'] = []

	def output_js(self):
		self.output.write('<script type="text/javascript">')
		for file_path in self.files['js']:
			if self.options['v']:
				print('Inserting javascript from', file_path)
			if self.options['m']:
				self.output.write(jsmin(self.resolve_path(file_path)[0]))
			else:
				self.output.write(self.resolve_path(file_path)[0])
		self.output.write('</script>')
		# Clear file queue for scripts in body of html
		self.files['js'] = []

	def encode(self, file, extension=None):
		self.output.write(extension + ';base64,' + str(b64encode(file), 'utf-8'))


def display_help():
	exit('Usage: html-compiler.py [-mv] file [output_file]')


def parse_args():
	option_map = {
		'verbose': 'v',
		'minify' : 'm',
	}
	options = Parser.default_options
	input_file, input_path, output_file = None, None, None
	initial_directory = getcwd()
	for arg in argv[1:]:
		if arg[0] == '-':
			if arg[1:] in option_map:
				options[option_map[arg[1:]]] = True
			else:
				for char in arg[1:]:
					if char in options:
						options[char] = True
					else:
						display_help()
		elif input_file:
			# Output directory is relative to initial directory
			# Find relative path from new directory (input_path)
			output_file = relpath(join(initial_directory, arg), input_path)
			if isfile(output_file):
				overwrite = ''
				while match('(y(es)?)|(no?)', overwrite):
					overwrite = input('Overwrite ' + output_file + '?').lower()
					if match('no?', overwrite):
						output_file = 'output.html'
			if splitext(output_file)[1] != '.html':
				output_file += '.html'
		elif isfile(arg):
			input_file = arg
			input_path = dirname(input_file)
			chdir(input_path)
			output_file = 'output.html'
		else:
			print('File not found')
			return
	if not input_file:
		display_help()
	return input_file, input_path, output_file, options


def main():
	input_file, input_path, output_file, options = parse_args()
	with open(output_file, 'w') as output:
		p = Parser(output, options)
		p.feed(open(input_file, 'r').read())

if __name__ == '__main__':
	main()