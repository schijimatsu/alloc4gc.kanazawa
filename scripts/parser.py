#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import re
import json
import codecs
def error(*objs):
  print("ERROR: ", *objs, end='\n', file=sys.stderr)

from bs4 import BeautifulSoup

def remove_ruby(element):
  replaced = element.text
  if element.__class__ and element.__class__.__name__ == 'Tag':
    for text in [rt.text for rt in element.find_all('rt')]:
      replaced = replaced.replace(text, '')

  return replaced

def to_csv(content, filename):
  soup = BeautifulSoup(content)
  indices = []
  for i, td in enumerate(soup.body.table.findAll('tr')[1].findAll('td')):
    if len([c for c in td.contents if not isinstance(c, str) or c.strip() != '']) > 0 and td.ruby and '街区' in td.ruby.contents:
      indices.append(i)

  lines = soup.body.table.findAll('tr')[2:]
  parsed = []
  errors = []
  rets = [None]*len(indices)
  for i, line in enumerate(lines):
    for iindex, igaiku in enumerate(indices):
      tds = line.findAll('td')
      try:
        if not rets[iindex]:
          rets[iindex] = list()
        pl = [remove_ruby(td).strip().replace('\n', '').replace(' ', '') for td in [tds[igaiku-1], tds[igaiku], tds[igaiku+1], tds[igaiku+2]]]
        if ''.join(pl) != '':
          rets[iindex].append(','.join(pl))
      except Exception as e:
        print('rets:%s, tds:%s, tds.length:%s, igaiku:%s, iindex:%s, ' %(rets, tds, len(tds), igaiku, iindex))
        print(e)
        sys.exit()

  ex = parsed.extend
  for ret in rets:
    ex(ret)
  
  return parsed, errors

class AddressTree(object):
  def __init__(self, csv):
    self.csv = [line.split(',') for line in csv.split('\n')]
    self.struct = None
  
  def get_as_json(self):
    return json.dumps(self.struct, ensure_ascii=False, indent=2, separators=(',', ': '))
  
  def structure(self):
    self.struct = AddressTree.Aza(self.csv).structure()
    return self
  
  class Node(object):
    def __init__(self, csv):
      self.csv = csv
      self.nodes = {}
      self.csv_child_nodes = None
    
    def normalize(self, s):
      t = dict((0xff00 + ch, 0x0020 + ch) for ch in range(0x5f))
      t[0x3000] = 0x0020
      return s.translate(t)

    def abnormalize(self, s):
      t = dict((0x0020 + ch, 0xff00 + ch) for ch in range(0x5f))
      t[0x0020] = 0x3000
      return s.translate(t)
        
  class Chiku(Node):
    def structure(self):
      for record in self.csv:
        try:
          if record[3] != '':
            return record[3]
        except Exception as e:
          print('Error %s, record:%s,' %(e, record))
          sys.exit()
      
      return 'No Chiku'
  
  class Banchi(Node):
    def __init__(self, gaiku, csv):
      AddressTree.Node.__init__(self, csv)
      self.gaiku = gaiku
    
    def add_node(self, key, node):
      if key == '別記以外' or key == '上記以外':
        self.gaiku.nodes['others'] = AddressTree.Chiku(node).structure()
      else:
        self.nodes[key] = AddressTree.Chiku(node).structure()

      self.csv_child_nodes = None

    def check_pattern_number(self, regexp, number, node, start=None, end=None, prefix=None):
      m = re.compile(regexp).match(number)
      if m:
        _prefix = m.groups()[prefix] if prefix is not None else ''
        if start is not None and end is not None:
          for i in range(int(m.groups()[start]), int(m.groups()[end])):
            self.add_node('%s%d' %(_prefix, i), node)
        else:
          self.add_node('%s%s' %(_prefix, number), node)
        
        return True
      else:
        return False

    def structure(self):
      if len(self.csv) == 1:
        self.add_node(self.normalize(self.csv[0][2]), self.csv)
      else:
        temp_banchi = None
        temp_others = None
        for record in self.csv:
          number = record[2]
          if number != '':
            check = False
            conditions = (
              ('^[0-9]+$', {}), 
              ('^([0-9]+?)〜([0-9]+)$', {'start': 0, 'end': 1}), 
              ('^([^0-9]+?)([0-9]+?)〜([0-9]+)$', {'start': 1, 'end': 2, 'prefix': 0}), 
            )
            for c in conditions:
              if self.check_pattern_number(c[0], number, [record], **c[1]):
                check = True
                break
            
            if not check:
              if re.compile('^([0-9]+?)〜$').match(number) or re.compile('^([^0-9]+?)([0-9]+?)〜$').match(number):
                self.add_node(number, [record])
              elif re.compile('.*?、.*').match(number):
                for i in number.split('、'):
                  if i != '':
                    self.add_node(self.normalize(str(i)), [record])
              elif re.compile('.*?､.*').match(number):
                for i in number.split('､'):
                  if i != '':
                    self.add_node(self.normalize(str(i)), [record])
              elif number == '別記以外' or number == '上記以外':
                self.add_node(self.normalize(number), [record])
              else:
                self.add_node(self.normalize(number), [record])
                print('Error Banchi.no_pattern. %s,%s' %(number, record))
          else:
            if self.csv_child_nodes is not None:
              self.csv_child_nodes.append(record)
            else:
              self.csv_child_nodes = [record]

        if self.csv_child_nodes is not None:
          self.add_node(self.normalize(self.csv_child_nodes[0][2]), self.csv_child_nodes)

      return self.nodes if len(self.nodes) > 0 else None
  
  class Gaiku(Node):
    def structure(self):
      if len(self.csv) == 1:
        self.nodes[self.normalize(self.csv[0][1])] = AddressTree.Banchi(self, self.csv).structure()
      else:
        temp_gaiku = None
        for record in self.csv:
          if record[1] != '':
            if record[1] == '〜':
              if self.csv_child_nodes:
                temp_gaiku = self.csv_child_nodes[0]
                self.csv_child_nodes.append(record)
              else:
                print('Error Gaiku.~')
            elif temp_gaiku:
              if self.csv_child_nodes is not None:
                self.csv_child_nodes.append(record)
                for i in range(int(temp_gaiku[1]), int(record[1])+1):
                  self.nodes[str(i)] = AddressTree.Banchi(self, [self.csv_child_nodes[1]]).structure()
              else:
                print('Error Gaiku.temp_gaiku')
              temp_gaiku = None
              self.csv_child_nodes = None
            else:
              if self.csv_child_nodes is None:
                self.csv_child_nodes = [record]
              else:
                self.nodes[self.normalize(self.csv_child_nodes[0][1])] = AddressTree.Banchi(self, self.csv_child_nodes).structure()
                self.csv_child_nodes = [record]
          elif self.csv_child_nodes is not None:
            self.csv_child_nodes.append(record)
          else:
            self.csv_child_nodes = [record]
        
        if self.csv_child_nodes is not None:
          self.nodes[self.normalize(self.csv_child_nodes[0][1])] = AddressTree.Banchi(self, self.csv_child_nodes).structure()
    
      self.nodes = dict((k, v) for k, v in self.nodes.items() if v is not None)
      return self.nodes if len(self.nodes) > 0 else None
  
  class Aza(Node):
    def structure(self):
      for record in self.csv:
        if record[0] != '':
          if self.csv_child_nodes is None:
            self.csv_child_nodes = [record]
          else:
            key = self.abnormalize(self.csv_child_nodes[0][0])
            if key in self.nodes:
              self.nodes[key].update(AddressTree.Gaiku(self.csv_child_nodes).structure())
            else:
              self.nodes[key] = AddressTree.Gaiku(self.csv_child_nodes).structure()
            self.csv_child_nodes = [record]
        elif self.csv_child_nodes is not None:
          self.csv_child_nodes.append(record)
        else:
          print('Error Aza')
      
      if self.csv_child_nodes is not None:
        key = self.abnormalize(self.csv_child_nodes[0][0])
        if key in self.nodes:
          self.nodes[key].update(AddressTree.Gaiku(self.csv_child_nodes).structure())
        else:
          self.nodes[key] = AddressTree.Gaiku(self.csv_child_nodes).structure()

      self.nodes = dict((k, v) for k, v in self.nodes.items() if v is not None)
      return self.nodes if len(self.nodes) > 0 else None

def step1(path, name, to):
  whole_of_csv = []
  for i in range(2, 10):
    item = 'utf8.00%s.html' % i
    name, ext = os.path.splitext(item)
  
    csv, errors = (None, None)
    with open(os.path.abspath(os.path.join(path, item)), 'r') as f:
      csv, errors = to_csv(f.read(), item)
  
    whole_of_csv.append('\n'.join(csv))
    with open(os.path.abspath(os.path.join(to, name+'.csv')), 'w') as f:
      f.write('\n'.join(csv))
  
    if len(errors) > 0:
      with open(os.path.abspath(os.path.join(to, name+'.err')), 'w') as f:
        f.write('\n'.join(errors))
  
  with open(os.path.abspath(os.path.join(to, 'whole.csv')), 'w') as f:
    f.write('\n'.join(whole_of_csv))

def step2(path, name, to):
  with open(os.path.abspath(os.path.join(to, 'whole.csv')), 'r') as f:
    structured = AddressTree(f.read()).structure()
    
    with codecs.open(os.path.abspath(os.path.join(to, 'whole.json')), 'w') as f:
      f.write(structured.get_as_json())

def main(path='.', name='utf8.002.html', to='.'):
  # step1(path, name, to)
  step2(path, name, to)


if __name__ == '__main__':
  main(*(sys.argv[1:] if len(sys.argv) > 1 else []))