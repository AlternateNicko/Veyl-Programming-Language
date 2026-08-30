"""
string_toolkit.py
==================

A large, dependency-free (standard-library only) Python toolkit for string
manipulation, analysis, validation, and transformation.

Usage:
    All methods are @staticmethod, so you can call them either way:

        from string_toolkit import StringToolkit as st
        st.snake_case("Hello World")

        st = StringToolkit()
        st.snake_case("Hello World")

Categories:
    - Search & Query        : find_all, find_words, find_after, find_before,
                               contains_any, contains_all, startswith_any,
                               endswith_any, multi_split
    - Extraction             : extract_emails, extract_url, extract_numericals,
                               extract_integers, extract_decimals, extract_dates,
                               extract_encloser
    - Similarity             : similarity (+ levenshtein_distance,
                               damerau_levenshtein_distance, hamming_distance,
                               jaro_similarity, jaro_winkler_similarity,
                               cosine_similarity, sorensen_dice,
                               jaccard_similarity, longest_common_substring,
                               longest_common_subsequence)
    - Case conversion         : snake_case, camel_case, pascal_case, kebab_case,
                               screaming_snake_case, dot_case, path_case,
                               alternating_case, detect_case
    - Masking / Redaction     : mask, redact, mask_emails, mask_urls, mask_numbers
    - Formatting              : wrap, indent, dedent, align_left, align_right,
                               align_center, box, column, justify, number_lines,
                               replace_between
    - Encoding / Decoding     : base64_encode/decode, hex_encode/decode,
                               url_encode/decode, html_encode/decode
    - Ciphers                 : rot13, atbash, reverse_words, bacon
    - Corrections             : detect_typo, autocorrect, fuzzy_search
    - Unicode                 : unicode_info, unicode_name, codepoints,
                               from_codepoints, normalize_unicode, remove_accents,
                               is_emoji, emoji_count, graphemes
    - Statistics              : stats
    - Diffs                   : diff_lines, diff_words, diff_chars, patch
    - Parsing                 : parse_kv
    - Validation              : is_email, is_url, is_uuid, is_ipv4, is_ipv6,
                               is_json, is_xml, is_base64, validate_email,
                               validate_url, validate_ip, validate_uuid,
                               validate_hex, validate_json
    - Misc                    : reverse_words, shuffle, scramble_words,
                               letter_frequency
"""

import re
import math
import random
import base64
import codecs
import difflib
import html
import json
import socket
import textwrap
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter


class StringToolkit:
    """A large collection of string utilities. All methods are static."""

    # ------------------------------------------------------------------
    # Shared compiled patterns / lookup tables
    # ------------------------------------------------------------------
    EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    URL_RE = re.compile(r'(?:https?://|www\.)[^\s<>"\')]+')
    INT_RE = re.compile(r'-?\d+')
    DECIMAL_RE = re.compile(r'-?\d+\.\d+')
    NUMERIC_RE = re.compile(r'-?\d+\.\d+|-?\d+')

    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F300-\U0001FAFF"   # symbols, pictographs, emoticons, transport, supplemental
        "\U00002600-\U000026FF"   # misc symbols
        "\U00002700-\U000027BF"   # dingbats
        "\U0001F1E6-\U0001F1FF"   # regional indicators (flags)
        "]+", flags=re.UNICODE
    )

    # Modern 26-letter unique-code variant of Bacon's cipher (5-bit A/B code).
    # (Traditional Bacon's cipher shares codes for I/J and U/V; this variant
    # gives every letter of the modern alphabet a unique code.)
    BACON_MAP = {chr(65 + i): format(i, '05b').replace('0', 'A').replace('1', 'B')
                 for i in range(26)}
    BACON_MAP_REVERSE = {v: k for k, v in BACON_MAP.items()}

    # Small built-in word list used only as a lightweight demo dictionary for
    # detect_typo(). For real spell-checking, swap this out for a proper
    # dictionary / library (e.g. pyspellchecker, enchant).
    COMMON_WORDS = set("""
        the be to of and a in that have i it for not on with he as you do at
        this but his by from they we say her she or an will my one all would
        there their what so up out if about who get which go me when make
        can like time no just him know take people into year your good some
        could them see other than then now look only come its over think
        also back after use two how our work first well way even new want
        because any these give day most us is are was were been being has
        had did does doing yes hello world example test string tool python
        code file data value list dict function method class object
        """.split())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _as_list(target_delimiters):
        """Normalize a single delimiter string or a list of delimiters into a list."""
        if isinstance(target_delimiters, str):
            return [target_delimiters]
        return list(target_delimiters)

    @staticmethod
    def _split_words(s):
        """Split an arbitrary-case string (camelCase, snake_case, kebab-case,
        space separated, etc.) into a list of lowercase word tokens."""
        if not s:
            return []
        s = re.sub(r'[_\-\.\/\s]+', ' ', s)
        s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', s)
        s = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', s)
        return [w.lower() for w in s.split()]

    @staticmethod
    def _count_syllables(word):
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e') and count > 1:
            count -= 1
        return max(count, 1)

    # ==================================================================
    # SEARCH & QUERY
    # ==================================================================
    @staticmethod
    def find_all(string, target_delimiters):
        """Return a sorted list of every starting index of every delimiter
        (single string or list of strings) found in `string`."""
        indices = []
        for d in StringToolkit._as_list(target_delimiters):
            if not d:
                continue
            start = 0
            while True:
                idx = string.find(d, start)
                if idx == -1:
                    break
                indices.append(idx)
                start = idx + 1
        return sorted(indices)

    @staticmethod
    def find_words(string, target):
        """Return starting indices of whole-word occurrences of `target`."""
        return [m.start() for m in re.finditer(r'\b' + re.escape(target) + r'\b', string)]

    @staticmethod
    def find_after(string, target, target_after):
        """Return a list of substrings that appear immediately after each
        occurrence of `target`, up to (but not including) the next
        occurrence of `target_after`. If `target_after` isn't found after a
        given `target`, the remainder of the string is returned for that match."""
        results = []
        start = 0
        while True:
            idx = string.find(target, start)
            if idx == -1:
                break
            after_idx = idx + len(target)
            end_idx = string.find(target_after, after_idx)
            if end_idx == -1:
                results.append(string[after_idx:])
                break
            results.append(string[after_idx:end_idx])
            start = end_idx + len(target_after)
        return results

    @staticmethod
    def find_before(string, target, target_before):
        """Return a list of substrings that appear immediately before each
        occurrence of `target`, after the closest preceding occurrence of
        `target_before`. If `target_before` isn't found before a given
        `target`, everything from the start of the string is returned."""
        results = []
        search_start = 0
        while True:
            idx = string.find(target, search_start)
            if idx == -1:
                break
            before_idx = string.rfind(target_before, 0, idx)
            if before_idx == -1:
                results.append(string[:idx])
            else:
                results.append(string[before_idx + len(target_before):idx])
            search_start = idx + len(target)
        return results

    @staticmethod
    def contains_any(string, target_delimiters):
        return any(d in string for d in StringToolkit._as_list(target_delimiters))

    @staticmethod
    def contains_all(string, target_delimiters):
        return all(d in string for d in StringToolkit._as_list(target_delimiters))

    @staticmethod
    def startswith_any(string, target_delimiters):
        return string.startswith(tuple(StringToolkit._as_list(target_delimiters)))

    @staticmethod
    def endswith_any(string, target_delimiters):
        return string.endswith(tuple(StringToolkit._as_list(target_delimiters)))

    @staticmethod
    def multi_split(string, target_delimiters):
        """Split `string` on any of several delimiters (a list or a single string)."""
        delims = StringToolkit._as_list(target_delimiters)
        pattern = '|'.join(re.escape(d) for d in delims if d)
        if not pattern:
            return [string]
        return re.split(pattern, string)

    # ==================================================================
    # EXTRACTION
    # ==================================================================
    @staticmethod
    def extract_emails(text):
        return StringToolkit.EMAIL_RE.findall(text)

    @staticmethod
    def extract_url(text):
        urls = StringToolkit.URL_RE.findall(text)
        return [u.rstrip('.,;:!?)') for u in urls]

    @staticmethod
    def extract_numericals(text):
        """Extract all numbers (ints and floats), typed appropriately."""
        result = []
        for m in StringToolkit.NUMERIC_RE.findall(text):
            result.append(float(m) if '.' in m else int(m))
        return result

    @staticmethod
    def extract_integers(text):
        """Extract integers only (numbers that are part of a decimal are excluded)."""
        text_wo_decimals = StringToolkit.DECIMAL_RE.sub(' ', text)
        return [int(x) for x in StringToolkit.INT_RE.findall(text_wo_decimals)]

    @staticmethod
    def extract_decimals(text):
        return [float(x) for x in StringToolkit.DECIMAL_RE.findall(text)]

    @staticmethod
    def extract_dates(text, format="dd/mm/yy"):
        """Extract date-like substrings matching a simple format template
        made of `dd`, `mm`, `yy`, `yyyy` tokens plus literal separators,
        e.g. "dd/mm/yyyy", "mm-dd-yy", "yyyy.mm.dd"."""
        tokens = re.findall(r'yyyy|yy|mm|dd|[^a-zA-Z]+', format)
        token_regex = {'yyyy': r'\d{4}', 'yy': r'\d{2}', 'mm': r'\d{2}', 'dd': r'\d{2}'}
        pattern_parts = [token_regex.get(tok, re.escape(tok)) for tok in tokens]
        pattern = ''.join(pattern_parts)
        return re.findall(pattern, text)

    @staticmethod
    def extract_encloser(text, left_encloser, right_encloser):
        """Extract all substrings found between `left_encloser` and `right_encloser`."""
        pattern = re.escape(left_encloser) + r'(.*?)' + re.escape(right_encloser)
        return re.findall(pattern, text, re.DOTALL)

    # ==================================================================
    # SIMILARITY
    # ==================================================================
    @staticmethod
    def levenshtein_distance(s1, s2):
        m, n = len(s1), len(s2)
        if m == 0:
            return n
        if n == 0:
            return m
        prev = list(range(n + 1))
        for i in range(1, m + 1):
            curr = [i] + [0] * n
            for j in range(1, n + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
            prev = curr
        return prev[n]

    @staticmethod
    def damerau_levenshtein_distance(s1, s2):
        """Optimal string alignment variant of Damerau-Levenshtein distance
        (handles adjacent transpositions in addition to insert/delete/substitute)."""
        len1, len2 = len(s1), len(s2)
        d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                d[i][j] = min(
                    d[i - 1][j] + 1,
                    d[i][j - 1] + 1,
                    d[i - 1][j - 1] + cost,
                )
                if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)
        return d[len1][len2]

    @staticmethod
    def hamming_distance(s1, s2):
        if len(s1) != len(s2):
            raise ValueError("Hamming distance requires equal-length strings")
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

    @staticmethod
    def jaro_similarity(s1, s2):
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        match_distance = max(0, max(len1, len2) // 2 - 1)
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        matches = 0
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        if matches == 0:
            return 0.0
        k = 0
        transpositions = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        transpositions //= 2
        return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3

    @staticmethod
    def jaro_winkler_similarity(s1, s2, p=0.1, max_prefix=4):
        jaro_sim = StringToolkit.jaro_similarity(s1, s2)
        prefix_len = 0
        for c1, c2 in zip(s1, s2):
            if c1 == c2:
                prefix_len += 1
                if prefix_len == max_prefix:
                    break
            else:
                break
        return jaro_sim + prefix_len * p * (1 - jaro_sim)

    @staticmethod
    def cosine_similarity(s1, s2):
        """Character-frequency based cosine similarity."""
        vec1, vec2 = Counter(s1), Counter(s2)
        common = set(vec1) | set(vec2)
        dot = sum(vec1.get(ch, 0) * vec2.get(ch, 0) for ch in common)
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    @staticmethod
    def sorensen_dice(s1, s2):
        """Bigram-based Sørensen-Dice coefficient."""
        def bigrams(s):
            return [s[i:i + 2] for i in range(len(s) - 1)]
        b1, b2 = bigrams(s1), bigrams(s2)
        if not b1 and not b2:
            return 1.0
        if not b1 or not b2:
            return 0.0
        c1, c2 = Counter(b1), Counter(b2)
        overlap = sum((c1 & c2).values())
        return 2 * overlap / (len(b1) + len(b2))

    @staticmethod
    def jaccard_similarity(s1, s2):
        """Word-set based Jaccard similarity."""
        set1, set2 = set(s1.split()), set(s2.split())
        if not set1 and not set2:
            return 1.0
        return len(set1 & set2) / len(set1 | set2)

    @staticmethod
    def longest_common_substring(s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        longest, end_idx = 0, 0
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > longest:
                        longest = dp[i][j]
                        end_idx = i
        return s1[end_idx - longest:end_idx]

    @staticmethod
    def longest_common_subsequence(s1, s2):
        m, n = len(s1), len(s2)
        dp = [[''] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + s1[i - 1]
                else:
                    dp[i][j] = dp[i - 1][j] if len(dp[i - 1][j]) >= len(dp[i][j - 1]) else dp[i][j - 1]
        return dp[m][n]

    @staticmethod
    def similarity(text1, text2, method='levenshtein'):
        """Compute a 0-1 similarity score between two strings.

        method: one of 'levenshtein', 'damerau_levenshtein', 'hamming',
                'jaro', 'jaro_winkler', 'cosine', 'sorensen_dice',
                'jaccard', 'lcs', 'lcsubstring'
        """
        method = method.lower().replace('-', '_')
        max_len = max(len(text1), len(text2))

        if method == 'levenshtein':
            dist = StringToolkit.levenshtein_distance(text1, text2)
            return 1 - dist / max_len if max_len else 1.0
        elif method == 'damerau_levenshtein':
            dist = StringToolkit.damerau_levenshtein_distance(text1, text2)
            return 1 - dist / max_len if max_len else 1.0
        elif method == 'hamming':
            dist = StringToolkit.hamming_distance(text1, text2)
            return 1 - dist / len(text1) if text1 else 1.0
        elif method == 'jaro':
            return StringToolkit.jaro_similarity(text1, text2)
        elif method == 'jaro_winkler':
            return StringToolkit.jaro_winkler_similarity(text1, text2)
        elif method == 'cosine':
            return StringToolkit.cosine_similarity(text1, text2)
        elif method in ('sorensen_dice', 'dice'):
            return StringToolkit.sorensen_dice(text1, text2)
        elif method == 'jaccard':
            return StringToolkit.jaccard_similarity(text1, text2)
        elif method in ('lcs', 'longest_common_subsequence'):
            lcs = StringToolkit.longest_common_subsequence(text1, text2)
            return len(lcs) / max_len if max_len else 1.0
        elif method in ('lcsubstring', 'longest_common_substring'):
            sub = StringToolkit.longest_common_substring(text1, text2)
            return len(sub) / max_len if max_len else 1.0
        else:
            raise ValueError(f"Unknown similarity method: {method}")

    # ==================================================================
    # CASE CONVERSION
    # ==================================================================
    @staticmethod
    def snake_case(string):
        return '_'.join(StringToolkit._split_words(string))

    @staticmethod
    def camel_case(string):
        words = StringToolkit._split_words(string)
        if not words:
            return ''
        return words[0] + ''.join(w.capitalize() for w in words[1:])

    @staticmethod
    def pascal_case(string):
        return ''.join(w.capitalize() for w in StringToolkit._split_words(string))

    @staticmethod
    def kebab_case(string):
        return '-'.join(StringToolkit._split_words(string))

    @staticmethod
    def screaming_snake_case(string):
        return '_'.join(w.upper() for w in StringToolkit._split_words(string))

    @staticmethod
    def dot_case(string):
        return '.'.join(StringToolkit._split_words(string))

    @staticmethod
    def path_case(string):
        return '/'.join(StringToolkit._split_words(string))

    @staticmethod
    def alternating_case(string):
        result = []
        upper = False
        for ch in string:
            if ch.isalpha():
                result.append(ch.upper() if upper else ch.lower())
                upper = not upper
            else:
                result.append(ch)
        return ''.join(result)

    @staticmethod
    def detect_case(string):
        if not string:
            return 'unknown'
        if re.fullmatch(r'[a-z0-9]+(_[a-z0-9]+)+', string):
            return 'snake_case'
        if re.fullmatch(r'[A-Z0-9]+(_[A-Z0-9]+)+', string):
            return 'SCREAMING_SNAKE_CASE'
        if re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)+', string):
            return 'kebab-case'
        if re.fullmatch(r'[a-z0-9]+(\.[a-z0-9]+)+', string):
            return 'dot.case'
        if re.fullmatch(r'[a-z0-9]+(/[a-z0-9]+)+', string):
            return 'path/case'
        if re.fullmatch(r'[a-z][a-zA-Z0-9]*', string) and any(c.isupper() for c in string):
            return 'camelCase'
        if re.fullmatch(r'[A-Z][a-zA-Z0-9]*', string) and string[1:] != string[1:].upper():
            return 'PascalCase'
        if string.islower():
            return 'lowercase'
        if string.isupper():
            return 'UPPERCASE'
        if string.istitle():
            return 'Title Case'
        return 'mixed/unknown'

    # ==================================================================
    # MASKING / REDACTION
    # ==================================================================
    @staticmethod
    def mask(string, int_visible):
        """Mask all but the last `int_visible` characters with '*'."""
        if int_visible >= len(string):
            return string
        hidden_len = len(string) - int_visible
        return '*' * hidden_len + string[hidden_len:]

    @staticmethod
    def redact(string, target):
        return string.replace(target, '[REDACTED]')

    @staticmethod
    def mask_emails(string):
        def _mask(m):
            email = m.group(0)
            name, domain = email.split('@', 1)
            masked_name = name[0] + '*' * (len(name) - 1) if len(name) > 1 else '*'
            return masked_name + '@' + domain
        return StringToolkit.EMAIL_RE.sub(_mask, string)

    @staticmethod
    def mask_urls(string):
        return StringToolkit.URL_RE.sub('[URL]', string)

    @staticmethod
    def mask_numbers(string):
        return re.sub(r'\d', '*', string)

    # ==================================================================
    # FORMATTING
    # ==================================================================
    @staticmethod
    def wrap(string, width):
        return textwrap.fill(string, width)

    @staticmethod
    def indent(string, width):
        prefix = ' ' * width
        return '\n'.join(prefix + line for line in string.split('\n'))

    @staticmethod
    def dedent(string, width):
        lines = string.split('\n')
        result = []
        for line in lines:
            stripped = 0
            while stripped < width and stripped < len(line) and line[stripped] == ' ':
                stripped += 1
            result.append(line[stripped:])
        return '\n'.join(result)

    @staticmethod
    def align_left(string, width=None):
        lines = string.split('\n')
        w = width or max(len(l) for l in lines)
        return '\n'.join(l.ljust(w) for l in lines)

    @staticmethod
    def align_right(string, width=None):
        lines = string.split('\n')
        w = width or max(len(l) for l in lines)
        return '\n'.join(l.rjust(w) for l in lines)

    @staticmethod
    def align_center(string, width=None):
        lines = string.split('\n')
        w = width or max(len(l) for l in lines)
        return '\n'.join(l.center(w) for l in lines)

    @staticmethod
    def box(string):
        lines = string.split('\n')
        width = max(len(l) for l in lines)
        top = '┌' + '─' * (width + 2) + '┐'
        bottom = '└' + '─' * (width + 2) + '┘'
        middle = ['│ ' + l.ljust(width) + '  │' for l in lines]
        return '\n'.join([top] + middle + [bottom])

    @staticmethod
    def column(string, split_by=','):
        rows = [line.split(split_by) for line in string.split('\n') if line]
        if not rows:
            return ''
        col_count = max(len(r) for r in rows)
        widths = [0] * col_count
        for r in rows:
            for i, cell in enumerate(r):
                widths[i] = max(widths[i], len(cell.strip()))
        lines = []
        for r in rows:
            padded = [cell.strip().ljust(widths[i]) for i, cell in enumerate(r)]
            while len(padded) < col_count:
                padded.append(' ' * widths[len(padded)])
            lines.append(' | '.join(padded))
        return '\n'.join(lines)

    @staticmethod
    def justify(string, width):
        lines = []
        for line in string.split('\n'):
            words = line.split()
            if len(words) <= 1:
                lines.append(line.ljust(width))
                continue
            total_chars = sum(len(w) for w in words)
            gaps = len(words) - 1
            total_spaces = max(width - total_chars, gaps)
            space_width, extra = divmod(total_spaces, gaps)
            result = words[0]
            for i, w in enumerate(words[1:], 1):
                spaces = space_width + (1 if i <= extra else 0)
                result += ' ' * spaces + w
            lines.append(result)
        return '\n'.join(lines)

    @staticmethod
    def number_lines(multi_string, start=1):
        lines = multi_string.split('\n')
        width = len(str(start + len(lines) - 1))
        return '\n'.join(f'{i:>{width}}: {line}' for i, line in enumerate(lines, start))

    @staticmethod
    def replace_between(string, encloser1, encloser2, replacement_str):
        pattern = re.escape(encloser1) + r'.*?' + re.escape(encloser2)
        return re.sub(pattern, encloser1 + replacement_str + encloser2, string, flags=re.DOTALL)

    # ==================================================================
    # ENCODING / DECODING
    # ==================================================================
    @staticmethod
    def base64_encode(string):
        return base64.b64encode(string.encode('utf-8')).decode('ascii')

    @staticmethod
    def base64_decode(string):
        return base64.b64decode(string.encode('ascii')).decode('utf-8')

    @staticmethod
    def hex_encode(string):
        return string.encode('utf-8').hex()

    @staticmethod
    def hex_decode(string):
        return bytes.fromhex(string).decode('utf-8')

    @staticmethod
    def url_encode(string):
        return urllib.parse.quote(string)

    @staticmethod
    def url_decode(string):
        return urllib.parse.unquote(string)

    @staticmethod
    def html_encode(string):
        return html.escape(string)

    @staticmethod
    def html_decode(string):
        return html.unescape(string)

    # ==================================================================
    # CIPHERS
    # ==================================================================
    @staticmethod
    def rot13(string):
        return codecs.encode(string, 'rot13')

    @staticmethod
    def atbash(string):
        result = []
        for ch in string:
            if ch.isupper():
                result.append(chr(ord('Z') - (ord(ch) - ord('A'))))
            elif ch.islower():
                result.append(chr(ord('z') - (ord(ch) - ord('a'))))
            else:
                result.append(ch)
        return ''.join(result)

    @staticmethod
    def reverse_words(string):
        return ' '.join(string.split()[::-1])

    @staticmethod
    def bacon(string, decode=False):
        """Encode text with a modern 26-letter unique-code Bacon cipher, or
        decode it back (decode=True, expects space-separated 5-letter A/B groups)."""
        if decode:
            groups = string.split()
            return ''.join(StringToolkit.BACON_MAP_REVERSE.get(g, '?') for g in groups)
        result = []
        for ch in string.upper():
            if ch in StringToolkit.BACON_MAP:
                result.append(StringToolkit.BACON_MAP[ch])
            elif ch != ' ':
                result.append(ch)
        return ' '.join(result)

    # ==================================================================
    # CORRECTIONS  (lightweight, dictionary-free demo implementations)
    # ==================================================================
    @staticmethod
    def detect_typo(string):
        """Flag words not present in a small built-in common-word list.
        This is a lightweight heuristic, not a full dictionary check --
        for production use, plug in a real dictionary/library."""
        words = re.findall(r"[A-Za-z']+", string)
        return [w for w in words if w.lower() not in StringToolkit.COMMON_WORDS and len(w) > 2]

    @staticmethod
    def autocorrect(string, custom_keywords: list):
        """Replace each word with its closest match from `custom_keywords`
        (only if a sufficiently close match exists)."""
        corrected = []
        for w in string.split():
            matches = difflib.get_close_matches(w, custom_keywords, n=1, cutoff=0.6)
            corrected.append(matches[0] if matches else w)
        return ' '.join(corrected)

    @staticmethod
    def fuzzy_search(string, choices, threshold=0.6):
        """Return entries from `choices` that fuzzily match `string`, sorted
        by similarity score (highest first). Requires a `choices` list to
        search against."""
        scored = []
        for c in choices:
            score = difflib.SequenceMatcher(None, string.lower(), c.lower()).ratio()
            if score >= threshold:
                scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ==================================================================
    # UNICODE
    # ==================================================================
    @staticmethod
    def unicode_info(string):
        return [{
            'char': ch,
            'codepoint': f'U+{ord(ch):04X}',
            'decimal': ord(ch),
            'name': unicodedata.name(ch, 'UNKNOWN'),
            'category': unicodedata.category(ch),
        } for ch in string]

    @staticmethod
    def unicode_name(string):
        return [unicodedata.name(ch, 'UNKNOWN') for ch in string]

    @staticmethod
    def codepoints(string):
        return [f'U+{ord(ch):04X}' for ch in string]

    @staticmethod
    def from_codepoints(string):
        """Reconstruct a string from space-separated codepoints, e.g.
        'U+0048 U+0065 U+006C' or '48 65 6C' (hex, with or without 'U+')."""
        tokens = string.replace('U+', '').split()
        return ''.join(chr(int(t, 16)) for t in tokens)

    @staticmethod
    def normalize_unicode(string, form='NFC'):
        return unicodedata.normalize(form, string)

    @staticmethod
    def remove_accents(string):
        nfkd = unicodedata.normalize('NFKD', string)
        return ''.join(ch for ch in nfkd if not unicodedata.combining(ch))

    @staticmethod
    def is_emoji(string):
        return bool(StringToolkit.EMOJI_PATTERN.fullmatch(string))

    @staticmethod
    def emoji_count(string):
        return sum(1 for ch in string if StringToolkit.EMOJI_PATTERN.fullmatch(ch))

    @staticmethod
    def graphemes(string):
        """Approximate grapheme-cluster splitting (base char + combining marks)."""
        clusters = []
        current = ''
        for ch in string:
            if unicodedata.combining(ch) and current:
                current += ch
            else:
                if current:
                    clusters.append(current)
                current = ch
        if current:
            clusters.append(current)
        return clusters

    # ==================================================================
    # STATISTICS
    # ==================================================================
    @staticmethod
    def stats(string):
        words = re.findall(r"[A-Za-z']+", string)
        char_freq = dict(Counter(string))
        word_freq = dict(Counter(w.lower() for w in words))
        sentences = [s.strip() for s in re.split(r'[.!?]+', string) if s.strip()]

        avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
        unique_words = len(set(w.lower() for w in words))
        vocab_density = unique_words / len(words) if words else 0
        avg_sentence_len = len(words) / len(sentences) if sentences else 0

        syllables = sum(StringToolkit._count_syllables(w) for w in words)
        if words and sentences:
            flesch = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllables / len(words))
        else:
            flesch = 0

        entropy = 0.0
        length = len(string)
        if length:
            for count in char_freq.values():
                p = count / length
                entropy -= p * math.log2(p)

        return {
            'character_frequency': char_freq,
            'word_frequency': word_freq,
            'average_word_length': round(avg_word_len, 2),
            'unique_words': unique_words,
            'vocabulary_density': round(vocab_density, 3),
            'average_sentence_length': round(avg_sentence_len, 2),
            'readability_flesch': round(flesch, 2),
            'entropy': round(entropy, 3),
        }

    # ==================================================================
    # DIFFS
    # ==================================================================
    @staticmethod
    def diff_lines(string1, string2):
        return list(difflib.unified_diff(string1.splitlines(), string2.splitlines(), lineterm=''))

    @staticmethod
    def diff_words(string1, string2):
        return list(difflib.ndiff(string1.split(), string2.split()))

    @staticmethod
    def diff_chars(string1, string2):
        return list(difflib.ndiff(list(string1), list(string2)))

    @staticmethod
    def patch(string1, string2):
        return ''.join(difflib.unified_diff(
            string1.splitlines(keepends=True),
            string2.splitlines(keepends=True),
            fromfile='original', tofile='modified',
        ))

    # ==================================================================
    # PARSING
    # ==================================================================
    @staticmethod
    def parse_kv(string, pair_sep=';', kv_sep='='):
        """Parse a 'key=value;key=value' style string into a dict."""
        result = {}
        for pair in string.split(pair_sep):
            pair = pair.strip()
            if not pair or kv_sep not in pair:
                continue
            k, v = pair.split(kv_sep, 1)
            result[k.strip()] = v.strip()
        return result

    # ==================================================================
    # VALIDATION
    # ==================================================================
    @staticmethod
    def is_email(string):
        return bool(re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', string))

    @staticmethod
    def is_url(string):
        return bool(re.fullmatch(r'https?://[^\s]+', string))

    @staticmethod
    def is_uuid(string):
        return bool(re.fullmatch(
            r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', string))

    @staticmethod
    def is_ipv4(string):
        parts = string.split('.')
        if len(parts) != 4:
            return False
        for p in parts:
            if not p.isdigit() or not 0 <= int(p) <= 255 or (len(p) > 1 and p[0] == '0'):
                return False
        return True

    @staticmethod
    def is_ipv6(string):
        try:
            socket.inet_pton(socket.AF_INET6, string)
            return True
        except (socket.error, OSError):
            return False

    @staticmethod
    def is_json(string):
        try:
            json.loads(string)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_xml(string):
        try:
            ET.fromstring(string)
            return True
        except ET.ParseError:
            return False

    @staticmethod
    def is_base64(string):
        if not string or len(string) % 4 != 0:
            return False
        if not re.fullmatch(r'[A-Za-z0-9+/]*={0,2}', string):
            return False
        try:
            base64.b64decode(string, validate=True)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_email(string):
        return {'valid': StringToolkit.is_email(string), 'value': string}

    @staticmethod
    def validate_url(string):
        valid = StringToolkit.is_url(string)
        info = {'valid': valid, 'value': string}
        if valid:
            parsed = urllib.parse.urlparse(string)
            info['scheme'] = parsed.scheme
            info['domain'] = parsed.netloc
        return info

    @staticmethod
    def validate_ip(string):
        is_v4 = StringToolkit.is_ipv4(string)
        is_v6 = False if is_v4 else StringToolkit.is_ipv6(string)
        version = 4 if is_v4 else (6 if is_v6 else None)
        return {'valid': is_v4 or is_v6, 'version': version, 'value': string}

    @staticmethod
    def validate_uuid(string):
        valid = StringToolkit.is_uuid(string)
        info = {'valid': valid, 'value': string}
        if valid:
            info['version'] = string[14]
        return info

    @staticmethod
    def validate_hex(string):
        valid = bool(re.fullmatch(r'[0-9a-fA-F]+', string)) and len(string) % 2 == 0
        return {'valid': valid, 'value': string}

    @staticmethod
    def validate_json(string):
        try:
            parsed = json.loads(string)
            return {'valid': True, 'value': parsed}
        except (ValueError, TypeError) as e:
            return {'valid': False, 'error': str(e)}

    # ==================================================================
    # MISC
    # ==================================================================
    @staticmethod
    def shuffle(string):
        chars = list(string)
        random.shuffle(chars)
        return ''.join(chars)

    @staticmethod
    def scramble_words(string):
        """Shuffle the middle letters of each word, keeping first/last letters fixed."""
        def scramble(word):
            if len(word) <= 3:
                return word
            middle = list(word[1:-1])
            random.shuffle(middle)
            return word[0] + ''.join(middle) + word[-1]
        return ' '.join(scramble(w) for w in string.split())

    @staticmethod
    def letter_frequency(string):
        return dict(Counter(ch.lower() for ch in string if ch.isalpha()))


# ==========================================================================
# Demo
# ==========================================================================
if __name__ == "__main__":
    st = StringToolkit()

    print(st.snake_case("Hello World Example"))          # hello_world_example
    print(st.camel_case("hello_world_example"))           # helloWorldExample
    print(st.pascal_case("hello-world-example"))          # HelloWorldExample
    print(st.reverse_words("hello beautiful world"))      # world beautiful hello
    print(st.box("Hello"))
    print(st.column("c1,c2,c3", split_by=","))            # c1 | c2 | c3
    print(st.mask("1234567890", 4))                        # ******7890
    print(st.similarity("kitten", "sitting", method="levenshtein"))
    print(st.extract_emails("contact us at hello@example.com or bye@test.org"))
    print(st.stats("The quick brown fox jumps over the lazy dog."))
