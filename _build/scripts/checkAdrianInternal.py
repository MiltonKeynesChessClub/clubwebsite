#!/usr/bin/env python3
"""Compare Adrian Elwin's internal-competitions pages with the club sheet and _data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html as htmlmod
import io
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin


ADRIAN_INDEX = "http://www.adrianelwin.co.uk/MiltonKeynes/Internal.html"
USER_AGENT = (
	"Mozilla/5.0 (compatible; MKChessClubAdrianSync/1.0; "
	"+https://www.miltonkeyneschessclub.co.uk/)"
)
REQUEST_TIMEOUT = 30

DROPPED_NAME_TOKENS = {
	"n", "g", "e", "j", "d", "c", "l", "h", "b", "k", "f",
	"ne", "od", "nod",
}
NAME_ALIASES = {
	"azeem mauf": "Azeem Maruf",
}
BYE_NAMES = {"", "bye", "tbc"}

HREF_PATTERNS = [
	("openswiss", "swiss", re.compile(r"^OpenSwiss(\d{2})Rd(\d+)\.html$", re.I)),
	("u1800swiss", "swiss", re.compile(r"^U1800Swiss(\d{2})Rd(\d+)\.html$", re.I)),
	("u1400swiss", "swiss", re.compile(r"^U1400Swiss(\d{2})Rd(\d+)\.html$", re.I)),
	("openko", "ko", re.compile(r"^OpenKO(\d{2})Rd(\d+)\.html$", re.I)),
	("u1800ko", "ko", re.compile(r"^U1800KO(\d{2})Rd(\d+)\.html$", re.I)),
	("championship", "championship", re.compile(r"^Championship(\d{2})\.html$", re.I)),
	("allplayallblitz", "blitz", re.compile(r"^AllPlayAll(\d{4})\.html$", re.I)),
	("ladder", "ladder", re.compile(r"^Ladder(\d{2})Results\.html$", re.I)),
	("ladder", "ladder", re.compile(r"^Ladder(\d{2})Positions\.html$", re.I)),
]

TAG_RE = re.compile(r"<[^>]+>", re.S)
DATE_COMMENT_RE = re.compile(r"<!Date:\s*([^>]+)>", re.I)
CELL_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.I | re.S)
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.I | re.S)
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.I | re.S)
H3_RE = re.compile(r"<h3\b[^>]*>(.*?)</h3>", re.I | re.S)
LIVE_HREF_RE = re.compile(r'<a\s+href="([^"]+)"', re.I)
DUMMY_HREF_RE = re.compile(r'<!a\s+href="([^"]+)"', re.I)
DEADLINE_RE = re.compile(
	r"to be played by\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})",
	re.I,
)
ORDINAL_DEADLINE_RE = re.compile(
	r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})"
)
MONTHS = {
	"january": 1, "jan": 1,
	"february": 2, "feb": 2,
	"march": 3, "mar": 3,
	"april": 4, "apr": 4,
	"may": 5,
	"june": 6, "jun": 6,
	"july": 7, "jul": 7,
	"august": 8, "aug": 8,
	"september": 9, "sep": 9, "sept": 9,
	"october": 10, "oct": 10,
	"november": 11, "nov": 11,
	"december": 12, "dec": 12,
}

COMPETITION_LABELS = {
	"openswiss": "Open Swiss",
	"u1800swiss": "Under 1800 Swiss",
	"u1400swiss": "Under 1400 Swiss",
	"openko": "Open Knockout",
	"u1800ko": "Under 1800 Knockout",
	"championship": "Championship",
	"allplayallblitz": "All-Play-All Blitz",
	"ladder": "Ladder",
}


class FetchError( RuntimeError ):
	pass


def fetch( url: str ) -> str:
	request = urllib.request.Request( url, headers={ "User-Agent": USER_AGENT } )
	try:
		with urllib.request.urlopen( request, timeout=REQUEST_TIMEOUT ) as response:
			raw = response.read()
	except urllib.error.URLError as error:
		raise FetchError( f"Failed to fetch {url}: {error}" ) from error

	for encoding in ( "utf-8", "latin-1" ):
		try:
			return raw.decode( encoding )
		except UnicodeDecodeError:
			continue
	return raw.decode( "latin-1", errors="replace" )


def visible_text( markup: str ) -> str:
	dates = DATE_COMMENT_RE.findall( markup )
	text = TAG_RE.sub( " ", markup )
	text = htmlmod.unescape( text )
	text = text.replace( "\xa0", " " ).replace( "\u00bd", "1/2" )
	text = re.sub( r"\s+", " ", text ).strip()
	return text


def cell_parts( markup: str ) -> tuple[ str, str | None ]:
	date = None
	match = DATE_COMMENT_RE.search( markup )
	if match:
		date = match.group( 1 ).strip()
	return visible_text( markup ), date


def parse_html_date( value: str | None ) -> str:
	if not value:
		return ""
	value = value.strip()
	match = re.match( r"(\d{1,2})/(\d{1,2})/(\d{4})$", value )
	if match:
		day, month, year = match.groups()
		return f"{int( day ):02d}/{int( month ):02d}/{year}"
	return value


def iso_deadline( day: str, month_name: str, year: str ) -> str:
	month = MONTHS.get( month_name.lower() )
	if not month:
		return "asap"
	return f"{int( year ):04d}-{month:02d}-{int( day ):02d}"


def year_from_yy( yy: str, fallback: int ) -> int:
	value = int( yy )
	if value >= 100:
		return value
	return 2000 + value


def repo_root_from_script() -> Path:
	return Path( __file__ ).resolve().parents[ 2 ]


def parse_active_internal_seasons( yaml_text: str ) -> list[ dict ]:
	seasons = []
	in_internal = False
	current: dict | None = None

	for raw_line in yaml_text.splitlines():
		line = raw_line.rstrip()
		if line.startswith( "  internal:" ):
			in_internal = True
			continue
		if in_internal and re.match( r"^  [a-z]", line ) and not line.startswith( "  -" ):
			break
		if not in_internal:
			continue
		season_match = re.match( r"^  - season:\s*(\d+)", line )
		if season_match:
			if current:
				seasons.append( current )
			current = { "season": int( season_match.group( 1 ) ), "active": False, "googlesheet": "" }
			continue
		if current is None:
			continue
		active_match = re.match( r"^    active:\s*(\w+)", line )
		if active_match:
			current[ "active" ] = active_match.group( 1 ).lower() == "true"
			continue
		sheet_match = re.match( r"^    googlesheet:\s*(\S+)", line )
		if sheet_match:
			current[ "googlesheet" ] = sheet_match.group( 1 )

	if current:
		seasons.append( current )

	return [ item for item in seasons if item[ "active" ] ]


class NameMatcher:
	def __init__( self, members_csv: Path ):
		self.by_key: dict[ tuple[ str, str ], str ] = {}
		self.by_last: dict[ str, list[ str ] ] = defaultdict( list )
		self.alias = { key: value for key, value in NAME_ALIASES.items() }

		with members_csv.open( newline="", encoding="utf-8" ) as handle:
			reader = csv.DictReader( handle )
			for row in reader:
				display = ( row.get( "name" ) or "" ).strip().strip( '"' )
				if not display:
					continue
				self._index( display, display )
				ecf = ( row.get( "ecfname" ) or "" ).strip().strip( '"' )
				if ecf:
					self._index( ecf, display )
					if "," in ecf:
						last, rest = [ part.strip() for part in ecf.split( ",", 1 ) ]
						self._index( f"{rest} {last}", display )

		for alias, display in list( self.alias.items() ):
			self._index( alias, display )

	def _index( self, raw: str, display: str ) -> None:
		key = name_key( raw )
		if key is None:
			return
		self.by_key[ key ] = display
		if display not in self.by_last[ key[ 1 ] ]:
			self.by_last[ key[ 1 ] ].append( display )

	def canonical( self, raw: str | None ) -> str:
		cleaned = visible_text( raw or "" )
		if cleaned.lower() in BYE_NAMES:
			return "Bye" if cleaned.lower() == "bye" or cleaned == "" else ""
		alias = self.alias.get( cleaned.lower() )
		if alias:
			return alias
		key = name_key( cleaned )
		if key is None:
			return cleaned
		if key in self.by_key:
			return self.by_key[ key ]
		matches = self.by_last.get( key[ 1 ], [] )
		if len( matches ) == 1:
			return matches[ 0 ]
		fuzzy = unique_close_last_name( key[ 1 ], self.by_last )
		if fuzzy and len( self.by_last[ fuzzy ] ) == 1:
			return self.by_last[ fuzzy ][ 0 ]
		if key[ 0 ]:
			return f"{key[ 0 ].title()} {key[ 1 ].title()}"
		return cleaned.strip()


def name_key( raw: str ) -> tuple[ str, str ] | None:
	text = htmlmod.unescape( raw or "" )
	text = text.replace( "'", " " ).replace( "'", " " ).replace( "'", " " )
	text = re.sub( r"[^A-Za-z0-9\s-]", " ", text )
	parts = [ part.lower() for part in text.split() if part ]
	if not parts:
		return None
	last = parts[ -1 ]
	firsts = []
	for part in parts[ :-1 ]:
		if part in DROPPED_NAME_TOKENS or len( part ) <= 2:
			continue
		firsts.append( part )
	first = firsts[ 0 ] if firsts else ""
	return first, last


def unique_close_last_name( last: str, by_last: dict[ str, list[ str ] ] ) -> str | None:
	if last in by_last:
		return last
	close = [ candidate for candidate in by_last if edit_distance( last, candidate ) == 1 ]
	if len( close ) == 1:
		return close[ 0 ]
	return None


def edit_distance( left: str, right: str ) -> int:
	if left == right:
		return 0
	if abs( len( left ) - len( right ) ) > 1:
		return 2
	if len( left ) == len( right ):
		return sum( a != b for a, b in zip( left, right ) )
	if len( left ) > len( right ):
		left, right = right, left
	for index in range( len( right ) ):
		if left == right[ :index ] + right[ index + 1: ]:
			return 1
	return 2


def is_unresolved( name: str ) -> bool:
	return "/" in ( name or "" )


def classify_href( href: str, section_year: int ) -> dict | None:
	filename = href.split( "/" )[ -1 ].split( "?" )[ 0 ]
	for slug, kind, pattern in HREF_PATTERNS:
		match = pattern.match( filename )
		if not match:
			continue
		groups = match.groups()
		if kind == "blitz":
			year = int( groups[ 0 ] )
			round_number = None
		elif kind == "championship":
			year = year_from_yy( groups[ 0 ], section_year )
			round_number = None
		elif kind == "ladder":
			year = year_from_yy( groups[ 0 ], section_year )
			round_number = None
		else:
			year = year_from_yy( groups[ 0 ], section_year )
			round_number = int( groups[ 1 ] )
		return {
			"slug": slug,
			"kind": kind,
			"year": year,
			"round": round_number,
			"filename": filename,
			"href": href,
		}
	return None


def parse_internal_index( html: str ) -> dict[ int, dict ]:
	sections: dict[ int, dict ] = {}
	matches = list( re.finditer( r"Club Competitions\s+(\d{4})", html ) )
	for index, match in enumerate( matches ):
		year = int( match.group( 1 ) )
		start = match.end()
		end = matches[ index + 1 ].start() if index + 1 < len( matches ) else len( html )
		chunk = html[ start:end ]
		live = []
		dummy = []
		seen_live = set()
		seen_dummy = set()
		for href in LIVE_HREF_RE.findall( chunk ):
			classified = classify_href( href, year )
			if classified and classified[ "filename" ] not in seen_live:
				classified[ "url" ] = urljoin( ADRIAN_INDEX, href )
				live.append( classified )
				seen_live.add( classified[ "filename" ] )
		for href in DUMMY_HREF_RE.findall( chunk ):
			classified = classify_href( href, year )
			if classified and classified[ "filename" ] not in seen_dummy:
				dummy.append( classified )
				seen_dummy.add( classified[ "filename" ] )
		sections[ year ] = { "live": live, "dummy": dummy }
	return sections


def extract_deadline( html: str ) -> str:
	text = visible_text( html )
	match = DEADLINE_RE.search( text )
	if not match:
		return ""
	return iso_deadline( match.group( 1 ), match.group( 2 ), match.group( 3 ) )


def decode_result_pair( white_result: str, black_result: str ) -> str:
	white = white_result.replace( " ", "" ).replace( "½", "1/2" )
	black = black_result.replace( " ", "" ).replace( "½", "1/2" )
	if white == "" and black == "":
		return "tbc"
	if white == "+" and black in { "-", "" }:
		return "1-def"
	if white in { "-", "" } and black == "+":
		return "def-1"
	if white == "1" and black == "0":
		return "1-0"
	if white == "0" and black == "1":
		return "0-1"
	if white == "1/2" and black == "1/2":
		return "1/2-1/2"
	return "tbc"


def normalize_result( raw: str ) -> str:
	value = ( raw or "" ).strip().lower()
	value = value.replace( "½", "1/2" ).replace( "\u00bd", "1/2" )
	mapping = {
		"tbc": "tbc",
		"": "tbc",
		"1-0": "1-0",
		"0-1": "0-1",
		"1/2-1/2": "1/2-1/2",
		"bye": "bye",
		"1/2 pt bye": "bye",
		"white defaulted": "def-1",
		"black defaulted": "1-def",
		"game defaulted": "def-def",
		"1-def": "1-def",
		"def-1": "def-1",
		"def-def": "def-def",
		"+": "1-def",
		"-": "def-1",
	}
	return mapping.get( value, value )


def result_is_complete( result: str ) -> bool:
	return normalize_result( result ) not in { "tbc", "" }


def parse_swiss_page( html: str, matcher: NameMatcher, page: dict ) -> dict:
	games = []
	for row in ROW_RE.findall( html ):
		if "!game" not in row.lower() and not re.search( r"<tr[^>]*!game", row, re.I ):
			# ROW_RE captures inside tr, so look at original via cells
			pass
		cells = CELL_RE.findall( row )
		if len( cells ) < 9:
			continue
		values = [ cell_parts( cell )[ 0 ] for cell in cells ]
		if values[ 0 ].lower() in { "", "white" } or not re.match( r"^\d+$", values[ 0 ] ):
			continue
		board = int( values[ 0 ] )
		white = matcher.canonical( values[ 1 ] )
		black = matcher.canonical( values[ 8 ] )
		white_result = values[ 4 ]
		black_result = values[ 6 ]
		date = values[ 10 ] if len( values ) > 10 else ""
		if white in { "", "Bye" } and black in { "", "Bye" }:
			continue
		if black in { "", "Bye" }:
			result = "bye"
			black = "Bye"
		else:
			result = decode_result_pair( white_result, black_result )
		games.append( {
			"board": board,
			"white": white,
			"black": black,
			"white_rating": values[ 2 ],
			"black_rating": values[ 9 ] if len( values ) > 9 else "",
			"date": parse_html_date( date ),
			"result": result,
			"unresolved": is_unresolved( values[ 1 ] ) or is_unresolved( values[ 8 ] ),
			"raw_white": values[ 1 ],
			"raw_black": values[ 8 ],
		} )

	# Fallback: some rows use `<tr !game N>` which ROW_RE still captures via inner html
	if not games:
		for match in re.finditer( r"<tr[^>]*!game[^>]*>(.*?)</tr>", html, re.I | re.S ):
			cells = CELL_RE.findall( match.group( 1 ) )
			if len( cells ) < 9:
				continue
			values = [ cell_parts( cell )[ 0 ] for cell in cells ]
			if not re.match( r"^\d+$", values[ 0 ] ):
				continue
			white = matcher.canonical( values[ 1 ] )
			black = matcher.canonical( values[ 8 ] )
			if white in { "", "Bye" } and black in { "", "Bye" }:
				continue
			if black in { "", "Bye" }:
				result = "bye"
				black = "Bye"
			else:
				result = decode_result_pair( values[ 4 ], values[ 6 ] )
			games.append( {
				"board": int( values[ 0 ] ),
				"white": white,
				"black": black,
				"white_rating": values[ 2 ],
				"black_rating": values[ 9 ] if len( values ) > 9 else "",
				"date": parse_html_date( values[ 10 ] if len( values ) > 10 else "" ),
				"result": result,
				"unresolved": is_unresolved( values[ 1 ] ) or is_unresolved( values[ 8 ] ),
				"raw_white": values[ 1 ],
				"raw_black": values[ 8 ],
			} )

	return {
		"games": games,
		"deadline": extract_deadline( html ),
		"round": page.get( "round" ),
	}


def parse_ko_page( html: str, matcher: NameMatcher, page: dict ) -> dict:
	headings = []
	for match in H2_RE.finditer( html ):
		title = visible_text( match.group( 1 ) )
		if "knockout" not in title.lower():
			continue
		headings.append( { "title": title, "start": match.start() } )

	sections = []
	for index, heading in enumerate( headings ):
		end = headings[ index + 1 ][ "start" ] if index + 1 < len( headings ) else len( html )
		chunk = html[ heading[ "start" ]:end ]
		plate = "plate" in heading[ "title" ].lower()
		round_match = re.search( r"round\s+(\d+)", heading[ "title" ], re.I )
		round_number = int( round_match.group( 1 ) ) if round_match else page.get( "round" )
		games = []
		for row_html in re.findall( r"<tr[^>]*!game[=\s]*(\d+)[^>]*>(.*?)</tr>", chunk, re.I | re.S ):
			cells = CELL_RE.findall( row_html[ 1 ] )
			values = [ cell_parts( cell )[ 0 ] for cell in cells ]
			if len( values ) < 5:
				continue
			left_raw = values[ 0 ]
			right_raw = values[ 4 ]
			left_result = values[ 1 ] if len( values ) > 1 else ""
			right_result = values[ 3 ] if len( values ) > 3 else ""
			if left_raw.lower() in { "", "result" } or left_raw.lower().startswith( "time control" ):
				continue
			unresolved = is_unresolved( left_raw ) or is_unresolved( right_raw )
			white = matcher.canonical( left_raw )
			black = matcher.canonical( right_raw )
			if black in { "", "Bye" } or right_raw.lower() == "bye":
				result = "bye"
				black = "Bye"
			else:
				result = decode_result_pair( left_result, right_result )
			games.append( {
				"white": white,
				"black": black,
				"date": "",
				"result": result,
				"unresolved": unresolved,
				"raw_white": left_raw,
				"raw_black": right_raw,
			} )
		sections.append( {
			"pool": "plate" if plate else "main",
			"round": round_number,
			"title": heading[ "title" ],
			"games": games,
		} )
	return { "sections": sections }


def championship_cell_result( text: str ) -> str | None:
	value = text.replace( " ", "" )
	if value in { "", "w", "b", "xxxx", "score" }:
		return None
	if value in { "1", "+" }:
		return "1"
	if value in { "0", "-" }:
		return "0"
	if value in { "1/2", "½" }:
		return "1/2"
	if re.match( r"^\d+1/2$", value ) or re.match( r"^\d+$", value ):
		return None
	return None


def parse_championship_page( html: str, matcher: NameMatcher ) -> dict:
	pools: dict[ str, list ] = {}
	headings = []
	for match in H3_RE.finditer( html ):
		title = visible_text( match.group( 1 ) )
		headings.append( { "title": title, "start": match.start() } )

	for index, heading in enumerate( headings ):
		end = headings[ index + 1 ][ "start" ] if index + 1 < len( headings ) else len( html )
		chunk = html[ heading[ "start" ]:end ]
		pool = heading_to_pool( heading[ "title" ] )
		if not pool:
			continue
		table_match = re.search( r"<table\b[^>]*border=\"1\"[^>]*>(.*?)</table>", chunk, re.I | re.S )
		if not table_match:
			continue
		rows = [ CELL_RE.findall( row ) for row in ROW_RE.findall( table_match.group( 1 ) ) ]
		if not rows:
			continue
		header_cells = [ cell_parts( cell )[ 0 ] for cell in rows[ 0 ] ]
		players = []
		for cell in header_cells:
			if cell.lower() in { "", "score" } or re.match( r"^\d+$", cell ):
				continue
			if len( cell.split() ) >= 2:
				players.append( matcher.canonical( cell ) )
		if len( players ) < 2:
			continue
		games = []
		for row in rows[ 1: ]:
			values = [ cell_parts( cell ) for cell in row ]
			texts = [ item[ 0 ] for item in values ]
			if len( texts ) < 5:
				continue
			row_name = matcher.canonical( texts[ 1 ] )
			if row_name in { "", "Bye" } or not texts[ 1 ]:
				continue
			result_cells = values[ 4:4 + len( players ) ]
			for column, ( cell_text, cell_date ) in enumerate( result_cells ):
				if column >= len( players ):
					break
				opponent = players[ column ]
				if opponent == row_name:
					continue
				score = championship_cell_result( cell_text )
				if score is None:
					continue
				games.append( {
					"white": row_name,
					"black": opponent,
					"row_score": score,
					"date": parse_html_date( cell_date ),
					"result": championship_score_to_result( score ),
				} )
		pools[ pool ] = games
	return { "pools": pools }


def heading_to_pool( title: str ) -> str:
	text = title.strip().lower()
	if text.startswith( "final" ):
		return "final"
	match = re.search( r"pool\s+(\d+)", text )
	if match:
		return f"pool{match.group( 1 )}"
	return ""


def championship_score_to_result( score: str ) -> str:
	if score == "1":
		return "1-0"
	if score == "0":
		return "0-1"
	if score == "1/2":
		return "1/2-1/2"
	return "tbc"


def pair_key( left: str, right: str ) -> tuple[ str, str ]:
	return tuple( sorted( [ left, right ] ) )


def outcome_for_first( first: str, white: str, black: str, result: str ) -> str | None:
	result = normalize_result( result )
	if result in { "tbc", "" }:
		return None
	if result == "bye":
		return "bye" if first == white else None
	white_points = {
		"1-0": "1",
		"0-1": "0",
		"1/2-1/2": "1/2",
		"1-def": "1",
		"def-1": "0",
		"def-def": "0",
	}.get( result )
	if white_points is None:
		return None
	if first == white:
		return white_points
	if first == black:
		if white_points == "1":
			return "0"
		if white_points == "0":
			return "1"
		return "1/2"
	return None


def load_sheet_games( csv_text: str, matcher: NameMatcher ) -> dict:
	by_comp: dict = defaultdict( lambda: defaultdict( list ) )
	reader = csv.DictReader( io.StringIO( csv_text ) )
	for row in reader:
		slug = ( row.get( "Tournament" ) or "" ).strip()
		fmt = ( row.get( "Format" ) or "" ).strip()
		if not slug:
			continue
		white = matcher.canonical( row.get( "White" ) or "" )
		black = matcher.canonical( row.get( "Black" ) or "" )
		result = normalize_result( row.get( "Result" ) or "" )
		pool = ( row.get( "Pool" ) or "" ).strip()
		round_raw = ( row.get( "Round" ) or "" ).strip()
		board_raw = ( row.get( "Board" ) or "" ).strip()
		game = {
			"format": fmt,
			"pool": pool or "main",
			"round": int( round_raw ) if round_raw.isdigit() else 0,
			"board": int( board_raw ) if board_raw.isdigit() else 0,
			"white": white,
			"black": black if black else "Bye",
			"white_rating": ( row.get( "White rating" ) or "" ).strip(),
			"black_rating": ( row.get( "Black rating" ) or "" ).strip(),
			"date": ( row.get( "Date" ) or "" ).strip(),
			"result": result,
		}
		by_comp[ slug ][ "games" ].append( game )
		by_comp[ slug ][ "format" ] = fmt
	return by_comp


def read_csv_file( path: Path ) -> list[ dict ]:
	if not path.exists():
		return []
	with path.open( newline="", encoding="utf-8" ) as handle:
		return list( csv.DictReader( handle ) )


def load_data_season( data_root: Path, year: int, matcher: NameMatcher ) -> dict:
	season_dir = data_root / str( year )
	result: dict = {}
	if not season_dir.exists():
		return result
	for child in season_dir.iterdir():
		if not child.is_dir():
			continue
		slug = child.name
		entry = {
			"rounds": read_csv_file( child / "rounds.csv" ),
			"pairings": [],
			"has_dir": True,
		}
		if slug == "championship":
			for pool_dir in sorted( child.iterdir() ):
				if pool_dir.is_dir():
					for row in read_csv_file( pool_dir / "pairings.csv" ):
						entry[ "pairings" ].append( {
							"pool": pool_dir.name,
							"round": int( row.get( "round" ) or 0 or 0 ) if str( row.get( "round" ) or "" ).isdigit() else 0,
							"white": matcher.canonical( row.get( "white" ) or "" ),
							"black": matcher.canonical( row.get( "black" ) or "" ),
							"date": row.get( "date" ) or "",
							"result": normalize_result( row.get( "result" ) or "" ),
						} )
		else:
			for row in read_csv_file( child / "pairings.csv" ):
				entry[ "pairings" ].append( {
					"pool": row.get( "pool" ) or "main",
					"round": int( row.get( "round" ) or 0 ) if str( row.get( "round" ) or "" ).isdigit() else 0,
					"board": int( row.get( "board" ) or 0 ) if str( row.get( "board" ) or "" ).isdigit() else 0,
					"white": matcher.canonical( row.get( "white" ) or "" ),
					"black": matcher.canonical( row.get( "black" ) or "" ) or "Bye",
					"date": row.get( "date" ) or "",
					"result": normalize_result( row.get( "result" ) or "" ),
				} )
		result[ slug ] = entry
	return result


def sheet_rounds( games: list[ dict ], fmt: str ) -> set:
	rounds = set()
	for game in games:
		if fmt == "ko":
			rounds.add( ( game[ "pool" ], game[ "round" ] ) )
		else:
			rounds.add( game[ "round" ] )
	return rounds


def data_round_numbers( rounds_rows: list[ dict ], fmt: str ) -> set:
	found = set()
	for row in rounds_rows:
		if fmt == "ko":
			pool = row.get( "pool" ) or "main"
			number = row.get( "number" ) or ""
			if str( number ).isdigit():
				found.add( ( pool, int( number ) ) )
		else:
			number = row.get( "number" ) or ""
			if str( number ).isdigit():
				found.add( int( number ) )
	return found


def find_sheet_game( games: list[ dict ], white: str, black: str, round_number: int | None, pool: str | None, unordered: bool ) -> dict | None:
	for game in games:
		if round_number is not None and game[ "round" ] and game[ "round" ] != round_number:
			continue
		if pool and game.get( "pool" ) and game[ "pool" ] != pool:
			continue
		if game[ "white" ] == white and game[ "black" ] == black:
			return game
		if unordered and game[ "white" ] == black and game[ "black" ] == white:
			return game
	return None


def csv_row_for_game( slug: str, fmt: str, game: dict, pool: str = "", round_number: int = 0 ) -> str:
	pool_value = pool or game.get( "pool" ) or ""
	round_value = round_number or game.get( "round" ) or ""
	board = game.get( "board" ) or ""
	white = game.get( "white" ) or ""
	black = game.get( "black" ) or ""
	if black == "Bye":
		black = ""
	white_rating = re.sub( r"e$", "", str( game.get( "white_rating" ) or "" ) )
	black_rating = re.sub( r"e$", "", str( game.get( "black_rating" ) or "" ) )
	date = game.get( "date" ) or ""
	result = game.get( "result" ) or "tbc"
	if result == "bye" and not black:
		result = "bye"
	return ",".join( [
		slug,
		fmt,
		str( pool_value ),
		str( round_value ),
		str( board ),
		white,
		white_rating,
		black,
		black_rating,
		date,
		result,
	] )


def ko_round_name( pool: str, number: int, title: str = "" ) -> str:
	lower = ( title or "" ).lower()
	if "semi" in lower:
		return "Plate semi finals" if pool == "plate" else "Semi finals"
	if "final" in lower and "semi" not in lower:
		return "Plate final" if pool == "plate" else "Final / Plate Final"
	ordinals = { 1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth" }
	label = ordinals.get( number, f"Round {number}" )
	if pool == "plate":
		if number == 1:
			return "First round plate"
		if number == 2:
			return "Second round plate"
		return f"{label} round plate"
	if number >= 4:
		return "Final / Plate Final"
	return f"{label} round draw"


def match_winner( white: str, black: str, result: str ) -> str | None:
	value = normalize_result( result )
	if value in { "1-0", "1-def" }:
		return white
	if value in { "0-1", "def-1" }:
		return black
	if value == "1/2-1/2":
		return "draw"
	return None


def unique_ko_matches( games: list[ dict ] ) -> list[ dict ]:
	grouped: dict[ tuple[ str, str ], list[ dict ] ] = defaultdict( list )
	order = []
	for game in games:
		if game.get( "unresolved" ):
			continue
		if game.get( "black" ) in { "Bye", "" } or game.get( "result" ) == "bye":
			continue
		key = pair_key( game[ "white" ], game[ "black" ] )
		if key not in grouped:
			order.append( key )
		grouped[ key ].append( game )
	matches = []
	for key in order:
		rows = grouped[ key ]
		decisive = [
			row for row in rows
			if match_winner( row[ "white" ], row[ "black" ], row[ "result" ] ) not in { None, "draw" }
		]
		chosen = dict( decisive[ -1 ] if decisive else rows[ -1 ] )
		chosen[ "extra_games" ] = len( rows ) - 1
		matches.append( chosen )
	return matches


class Report:
	def __init__( self ):
		self.actions: list[ dict ] = []
		self.conflicts: list[ dict ] = []
		self.info: list[ dict ] = []

	def add( self, bucket: str, **kwargs ) -> None:
		getattr( self, bucket ).append( kwargs )

	def has_actions( self ) -> bool:
		return bool( self.actions or self.conflicts )


def compare_swiss(
	report: Report,
	season: int,
	slug: str,
	page: dict,
	parsed: dict,
	sheet_games: list[ dict ],
	data_entry: dict,
) -> None:
	label = COMPETITION_LABELS.get( slug, slug )
	url = page[ "url" ]
	round_number = parsed[ "round" ] or page.get( "round" )
	adrian_games = [ game for game in parsed[ "games" ] if not game[ "unresolved" ] ]
	if not adrian_games:
		return

	data_rounds = data_round_numbers( data_entry.get( "rounds", [] ), "swiss" )
	actions = []
	details = []
	csv_rows = []
	missing = []
	result_updates = []
	adrian_ahead = []
	we_ahead = []

	if round_number not in sheet_rounds( sheet_games, "swiss" ):
		actions.append(
			f"Add Round {round_number} pairings to the {season} Google Sheet "
			f"(Tournament=`{slug}`, Format=`swiss`)."
		)
		for game in adrian_games:
			csv_rows.append( csv_row_for_game( slug, "swiss", game, round_number=round_number ) )
			missing.append( format_game_line( game ) )
	else:
		for game in adrian_games:
			found = find_sheet_game( sheet_games, game[ "white" ], game[ "black" ], round_number, None, False )
			if found is None:
				missing.append( format_game_line( game ) )
				csv_rows.append( csv_row_for_game( slug, "swiss", game, round_number=round_number ) )
				continue
			if result_is_complete( game[ "result" ] ) and not result_is_complete( found[ "result" ] ):
				result_updates.append(
					f"{game['white']} vs {game['black']}: Adrian `{game['result']}`"
					f"{f' ({game['date']})' if game['date'] else ''}, sheet still `{found['result']}`"
				)
			elif result_is_complete( game[ "result" ] ) and result_is_complete( found[ "result" ] ):
				if normalize_result( game[ "result" ] ) != normalize_result( found[ "result" ] ):
					adrian_ahead.append(
						f"{game['white']} vs {game['black']}: Adrian `{game['result']}`, sheet `{found['result']}`"
					)
			elif not result_is_complete( game[ "result" ] ) and result_is_complete( found[ "result" ] ):
				we_ahead.append(
					f"{game['white']} vs {game['black']}: sheet `{found['result']}`, Adrian still tbc"
				)

		if missing:
			actions.append( f"Add the missing Round {round_number} pairings to the {season} Google Sheet." )
		if result_updates:
			actions.append( f"Update Round {round_number} results in the {season} Google Sheet from Adrian's page." )

	if round_number not in data_rounds:
		deadline = parsed.get( "deadline" ) or "asap"
		actions.append(
			f"Add a `{slug}/rounds.csv` row: `{round_number},false,true,{deadline}`."
		)

	if adrian_ahead:
		report.add(
			"conflicts",
			season=season,
			competition=label,
			title=f"{season} {label} — Round {round_number} result mismatch",
			source_url=url,
			actions=[ "Check the Google Sheet against Adrian's page and keep the correct result." ],
			details=adrian_ahead,
			csv_rows=[],
		)

	if actions:
		details = missing + result_updates
		report.add(
			"actions",
			season=season,
			competition=label,
			title=f"{season} {label} — Round {round_number} published",
			source_url=url,
			actions=actions,
			details=details,
			csv_rows=csv_rows,
		)
	elif we_ahead:
		report.add(
			"info",
			season=season,
			competition=label,
			title=f"{season} {label} — Round {round_number}: our sheet is ahead of Adrian",
			source_url=url,
			actions=[],
			details=we_ahead,
			csv_rows=[],
		)


def compare_ko(
	report: Report,
	season: int,
	slug: str,
	page: dict,
	parsed: dict,
	sheet_games: list[ dict ],
	data_entry: dict,
) -> None:
	label = COMPETITION_LABELS.get( slug, slug )
	url = page[ "url" ]
	data_rounds = data_round_numbers( data_entry.get( "rounds", [] ), "ko" )

	for section in parsed.get( "sections", [] ):
		pool = section[ "pool" ]
		round_number = section[ "round" ]
		unresolved = [ game for game in section[ "games" ] if game[ "unresolved" ] ]
		walkovers = [
			game[ "white" ]
			for game in section[ "games" ]
			if not game[ "unresolved" ] and ( game.get( "black" ) in { "Bye", "" } or game.get( "result" ) == "bye" )
		]
		adrian_games = unique_ko_matches( section[ "games" ] )
		actions = []
		csv_rows = []
		missing = []
		result_updates = []
		conflicts = []
		we_ahead = []

		if not adrian_games and not unresolved:
			continue

		sheet_has_round = ( pool, round_number ) in sheet_rounds( sheet_games, "ko" )
		if adrian_games and not sheet_has_round:
			actions.append(
				f"Add {pool} round {round_number} pairings to the {season} Google Sheet "
				f"(Tournament=`{slug}`, Format=`ko`, Pool=`{pool}`)."
			)
			for game in adrian_games:
				csv_rows.append( csv_row_for_game( slug, "ko", game, pool=pool, round_number=round_number ) )
				missing.append( format_game_line( game ) )
		else:
			for game in adrian_games:
				found = find_sheet_game( sheet_games, game[ "white" ], game[ "black" ], round_number, pool, True )
				if found is None:
					missing.append( format_game_line( game ) )
					csv_rows.append( csv_row_for_game( slug, "ko", game, pool=pool, round_number=round_number ) )
					continue
				adrian_winner = match_winner( game[ "white" ], game[ "black" ], game[ "result" ] )
				sheet_winner = match_winner( found[ "white" ], found[ "black" ], found[ "result" ] )
				if adrian_winner not in { None, "draw" } and sheet_winner is None:
					result_updates.append(
						f"{game['white']} vs {game['black']}: Adrian `{game['result']}`, sheet still `{found['result']}`"
					)
				elif adrian_winner == "draw" and sheet_winner not in { None, "draw" }:
					we_ahead.append(
						f"{game['white']} vs {game['black']}: sheet match result `{found['result']}`; "
						f"Adrian still shows `{game['result']}` (likely the first game of a KO tie)"
					)
				elif adrian_winner not in { None, "draw" } and sheet_winner == "draw":
					result_updates.append(
						f"{game['white']} vs {game['black']}: Adrian `{game['result']}`, sheet still `{found['result']}` "
						f"(possible first-game draw; update the match winner)"
					)
				elif adrian_winner not in { None, "draw" } and sheet_winner not in { None, "draw" }:
					if adrian_winner != sheet_winner:
						conflicts.append(
							f"{game['white']} vs {game['black']}: Adrian `{game['result']}` (winner {adrian_winner}), "
							f"sheet `{found['result']}` (winner {sheet_winner})"
						)
				elif adrian_winner is None and sheet_winner not in { None, "draw" }:
					we_ahead.append(
						f"{game['white']} vs {game['black']}: sheet `{found['result']}`, Adrian still tbc"
					)
			if missing:
				actions.append( f"Add the missing {pool} round {round_number} pairings to the {season} Google Sheet." )
			if result_updates:
				actions.append( f"Update {pool} round {round_number} results in the {season} Google Sheet." )

		if adrian_games and ( pool, round_number ) not in data_rounds:
			name = ko_round_name( pool, round_number, section.get( "title" ) or "" )
			plate = "true" if pool == "plate" else "false"
			actions.append(
				f"Add a `{slug}/rounds.csv` row: `{pool},{round_number},{name},false,true,{plate},`."
			)

		details_unresolved = [
			f"Unresolved on Adrian's page (leave until a winner is known): {game['raw_white']} vs {game['raw_black']}"
			for game in unresolved
		]
		walkover_details = []
		if walkovers and actions:
			walkover_details.append( "Adrian also lists byes/walkovers for: " + ", ".join( walkovers ) )

		if conflicts:
			report.add(
				"conflicts",
				season=season,
				competition=label,
				title=f"{season} {label} — {pool} round {round_number} result mismatch",
				source_url=url,
				actions=[ "Check the Google Sheet against Adrian's page and keep the correct result." ],
				details=conflicts,
				csv_rows=[],
			)

		if actions:
			report.add(
				"actions",
				season=season,
				competition=label,
				title=f"{season} {label} — {section['title']}",
				source_url=url,
				actions=actions,
				details=missing + result_updates + details_unresolved + walkover_details,
				csv_rows=csv_rows,
			)
		elif we_ahead or details_unresolved:
			report.add(
				"info",
				season=season,
				competition=label,
				title=f"{season} {label} — {section['title']}",
				source_url=url,
				actions=[],
				details=we_ahead + details_unresolved,
				csv_rows=[],
			)


def compare_championship(
	report: Report,
	season: int,
	page: dict,
	parsed: dict,
	sheet_games: list[ dict ],
) -> None:
	label = COMPETITION_LABELS[ "championship" ]
	url = page[ "url" ]
	sheet_by_pool: dict[ str, list ] = defaultdict( list )
	for game in sheet_games:
		sheet_by_pool[ game[ "pool" ] ].append( game )

	for pool, adrian_games in parsed.get( "pools", {} ).items():
		if not adrian_games:
			continue
		sheet_pool = sheet_by_pool.get( pool, [] )
		sheet_index = {}
		for game in sheet_pool:
			key = pair_key( game[ "white" ], game[ "black" ] )
			sheet_index[ key ] = game

		seen = set()
		missing = []
		result_updates = []
		conflicts = []
		we_ahead = []
		csv_rows = []

		for game in adrian_games:
			key = pair_key( game[ "white" ], game[ "black" ] )
			if key in seen:
				continue
			seen.add( key )
			first = key[ 0 ]
			adrian_out = outcome_for_first( first, game[ "white" ], game[ "black" ], game[ "result" ] )
			found = sheet_index.get( key )
			if found is None:
				missing.append( f"{game['white']} vs {game['black']} `{game['result']}` {game.get( 'date' ) or ''}".strip() )
				csv_rows.append( csv_row_for_game(
					"championship",
					"championship",
					{
						"white": game[ "white" ],
						"black": game[ "black" ],
						"date": game.get( "date" ) or "",
						"result": game[ "result" ],
					},
					pool=pool,
					round_number=1,
				) )
				continue
			sheet_out = outcome_for_first( first, found[ "white" ], found[ "black" ], found[ "result" ] )
			if adrian_out and sheet_out is None:
				result_updates.append(
					f"{game['white']} vs {game['black']}: Adrian `{game['result']}`"
					f"{f' ({game['date']})' if game.get('date') else ''}, sheet still `{found['result']}`"
				)
			elif adrian_out and sheet_out and adrian_out != sheet_out:
				conflicts.append(
					f"{game['white']} vs {game['black']}: Adrian `{game['result']}` (from {game['white']}'s score {game['row_score']}), "
					f"sheet `{found['white']} vs {found['black']}` `{found['result']}`"
				)
			elif adrian_out is None and sheet_out:
				we_ahead.append(
					f"{found['white']} vs {found['black']}: sheet `{found['result']}`, Adrian still unplayed"
				)

		actions = []
		if missing:
			actions.append( f"Add missing {pool} games to the {season} Google Sheet (Tournament=`championship`, Pool=`{pool}`)." )
		if result_updates:
			actions.append( f"Update {pool} results in the {season} Google Sheet from Adrian's crosstable." )
		if conflicts:
			report.add(
				"conflicts",
				season=season,
				competition=label,
				title=f"{season} {label} — {pool} result mismatch",
				source_url=url,
				actions=[ "Check the Google Sheet against Adrian's crosstable and keep the correct result." ],
				details=conflicts,
				csv_rows=[],
			)
		if actions:
			report.add(
				"actions",
				season=season,
				competition=label,
				title=f"{season} {label} — {pool}",
				source_url=url,
				actions=actions,
				details=missing + result_updates,
				csv_rows=csv_rows,
			)
		elif we_ahead:
			report.add(
				"info",
				season=season,
				competition=label,
				title=f"{season} {label} — {pool}: our sheet is ahead of Adrian",
				source_url=url,
				actions=[],
				details=we_ahead,
				csv_rows=[],
			)


def compare_existence(
	report: Report,
	season: int,
	page: dict,
	data_entry: dict | None,
	pages_root: Path,
) -> None:
	slug = page[ "slug" ]
	label = COMPETITION_LABELS.get( slug, slug )
	url = page[ "url" ]
	if slug == "allplayallblitz":
		data_dir = data_entry and data_entry.get( "has_dir" )
		page_file = pages_root / str( season ) / "all-play-all-blitz.markdown"
		actions = []
		if not data_dir:
			actions.append(
				f"Create `_data/results/internal/{season}/allplayallblitz/` from Adrian's page "
				f"(this format is not imported from the Google Sheet)."
			)
		if not page_file.exists():
			actions.append(
				f"Add `_pages/results/{season}/all-play-all-blitz.markdown` and link it from the {season} results index / navigation."
			)
		if actions:
			report.add(
				"actions",
				season=season,
				competition=label,
				title=f"{season} {label} page published",
				source_url=url,
				actions=actions,
				details=[],
				csv_rows=[],
			)
		return

	if slug == "ladder":
		pairings = ( data_entry or {} ).get( "pairings" ) or []
		if not pairings:
			report.add(
				"actions",
				season=season,
				competition=label,
				title=f"{season} {label} published on Adrian's site",
				source_url=url,
				actions=[
					f"Add ladder games to the {season} Google Sheet (Tournament=`ladder`, Format=`ladder`) "
					f"and ensure `_pages/results/{season}/ladder.markdown` exists."
				],
				details=[],
				csv_rows=[],
			)


def format_game_line( game: dict ) -> str:
	black = game.get( "black" ) or "Bye"
	result = game.get( "result" ) or "tbc"
	date = game.get( "date" ) or ""
	suffix = f" ({date})" if date else ""
	return f"{game.get('white')} vs {black} `{result}`{suffix}"


def sorted_findings( findings: Iterable[ dict ] ) -> list[ dict ]:
	return sorted(
		list( findings ),
		key=lambda item: (
			item.get( "season" ) or 0,
			item.get( "competition" ) or "",
			item.get( "title" ) or "",
		),
	)


def render_report( report: Report, generated: str ) -> str:
	lines = [
		"# Adrian internal competitions sync",
		"",
		f"Generated: {generated}",
		"",
	]
	if not report.actions and not report.conflicts:
		lines.append( "No actions needed." )
		if report.info:
			lines.append( "" )
			lines.append( "## Informational" )
			lines.append( "" )
			append_findings( lines, sorted_findings( report.info ) )
		return "\n".join( lines ) + "\n"

	if report.actions:
		lines.append( "## Actions needed" )
		lines.append( "" )
		append_findings( lines, sorted_findings( report.actions ) )
	if report.conflicts:
		lines.append( "## Conflicts" )
		lines.append( "" )
		append_findings( lines, sorted_findings( report.conflicts ) )
	if report.info:
		lines.append( "## Informational" )
		lines.append( "" )
		append_findings( lines, sorted_findings( report.info ) )
	return "\n".join( lines ) + "\n"


def append_findings( lines: list[ str ], findings: Iterable[ dict ] ) -> None:
	for item in findings:
		lines.append( f"### {item['title']}" )
		lines.append( "" )
		if item.get( "source_url" ):
			lines.append( f"Source: {item['source_url']}" )
			lines.append( "" )
		if item.get( "actions" ):
			lines.append( "**Suggested actions:**" )
			for index, action in enumerate( item[ "actions" ], start=1 ):
				lines.append( f"{index}. {action}" )
			lines.append( "" )
		if item.get( "csv_rows" ):
			lines.append( "Suggested Google Sheet rows:" )
			lines.append( "" )
			lines.append( "```" )
			lines.extend( item[ "csv_rows" ] )
			lines.append( "```" )
			lines.append( "" )
		if item.get( "details" ):
			for detail in item[ "details" ]:
				lines.append( f"- {detail}" )
			lines.append( "" )


def compare_season(
	report: Report,
	season: int,
	index_section: dict,
	sheet_by_comp: dict,
	data_by_comp: dict,
	matcher: NameMatcher,
	pages_root: Path,
) -> None:
	for page in index_section.get( "live", [] ):
		if page[ "year" ] != season and page[ "kind" ] != "blitz":
			continue
		if page[ "kind" ] == "blitz" and page[ "year" ] != season:
			continue
		slug = page[ "slug" ]
		kind = page[ "kind" ]
		sheet_entry = sheet_by_comp.get( slug, {} )
		sheet_games = sheet_entry.get( "games", [] )
		data_entry = data_by_comp.get( slug, {} )

		if kind in { "blitz", "ladder" }:
			compare_existence( report, season, page, data_entry, pages_root )
			continue

		html = fetch( page[ "url" ] )
		if kind == "swiss":
			parsed = parse_swiss_page( html, matcher, page )
			if not parsed[ "games" ]:
				print( f"Warning: no games parsed from {page['url']}", file=sys.stderr )
			compare_swiss( report, season, slug, page, parsed, sheet_games, data_entry )
		elif kind == "ko":
			parsed = parse_ko_page( html, matcher, page )
			if not any( section[ "games" ] for section in parsed.get( "sections", [] ) ):
				print( f"Warning: no games parsed from {page['url']}", file=sys.stderr )
			compare_ko( report, season, slug, page, parsed, sheet_games, data_entry )
		elif kind == "championship":
			parsed = parse_championship_page( html, matcher )
			if not any( parsed.get( "pools", {} ).values() ):
				print( f"Warning: no championship games parsed from {page['url']}", file=sys.stderr )
			compare_championship( report, season, page, parsed, sheet_games )


def main( argv: list[ str ] | None = None ) -> int:
	parser = argparse.ArgumentParser( description=__doc__ )
	parser.add_argument( "--repo-root", type=Path, default=repo_root_from_script() )
	parser.add_argument( "--index-url", default=ADRIAN_INDEX )
	parser.add_argument( "--season", type=int, action="append", dest="seasons" )
	args = parser.parse_args( argv )

	repo_root = args.repo_root.resolve()
	yaml_path = repo_root / "_data" / "mkchessclub.yml"
	members_path = repo_root / "_data" / "mkmembers.csv"
	data_root = repo_root / "_data" / "results" / "internal"
	pages_root = repo_root / "_pages" / "results"

	if not yaml_path.exists():
		print( f"Cannot find {yaml_path}", file=sys.stderr )
		return 1

	seasons = parse_active_internal_seasons( yaml_path.read_text( encoding="utf-8" ) )
	if args.seasons:
		wanted = set( args.seasons )
		seasons = [ item for item in seasons if item[ "season" ] in wanted ]
		if not seasons:
			print( "No matching active internal seasons.", file=sys.stderr )
			return 1

	matcher = NameMatcher( members_path )
	index_html = fetch( args.index_url )
	index_sections = parse_internal_index( index_html )
	report = Report()

	for season_info in seasons:
		season = season_info[ "season" ]
		section = index_sections.get( season )
		if not section:
			report.add(
				"actions",
				season=season,
				competition="Internal index",
				title=f"No {season} section found on Adrian's Internal.html",
				source_url=args.index_url,
				actions=[ "Check whether Adrian has renamed or removed the season heading." ],
				details=[],
				csv_rows=[],
			)
			continue

		sheet_by_comp: dict = {}
		if season_info.get( "googlesheet" ):
			try:
				sheet_text = fetch( season_info[ "googlesheet" ] )
				sheet_by_comp = load_sheet_games( sheet_text, matcher )
			except FetchError as error:
				print( f"Warning: {error}", file=sys.stderr )

		data_by_comp = load_data_season( data_root, season, matcher )
		compare_season( report, season, section, sheet_by_comp, data_by_comp, matcher, pages_root )

	generated = dt.datetime.now( dt.timezone.utc ).strftime( "%Y-%m-%d %H:%M UTC" )
	sys.stdout.write( render_report( report, generated ) )
	return 0


if __name__ == "__main__":
	try:
		sys.exit( main() )
	except FetchError as error:
		print( error, file=sys.stderr )
		sys.exit( 1 )
