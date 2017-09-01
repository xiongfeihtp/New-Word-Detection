#-*- coding:utf-8 -*-
"""
Chinese word segmentation algorithm with corpus
Author: "Xylander"
"""


import os
import re
import math
import time
from entropy import compute_entropy
from extract import extract_cadicateword,gen_bigram
import pandas as pd


class wordinfo(object):
    '''
    Record every candidate word information include left neighbors, right neighbors, frequency, PMI
    '''
    def __init__(self,text):
        super(wordinfo,self).__init__()
        self.text = text
        self.freq = 0.0
        self.left = []  #record left neighbors
        self.right = [] #record right neighbors
        self.pmi = 0

    def update_data(self,left,right):
        self.freq += 1.0
        if left:
            self.left.append(left)
        if right:
            self.right.append(right)

    def compute_indexes(self,length):
        #compute frequency of word,and left/right entropy
        self.freq /= length
        self.left = compute_entropy(self.left)
        self.right = compute_entropy(self.right)

    def compute_pmi(self,words_dict):
        #compute all kinds of combines for word
        sub_part = gen_bigram(self.text)
        if len(sub_part) > 0:
            self.pmi = min(map(lambda (left,right) : math.log(self.freq/words_dict[left].freq/words_dict[right].freq),sub_part))

class segdocument(object):
    '''
    Main class for Chinese word segmentation
    1. Generate words from a long enough document
    2. Do the segmentation work with the document
    reference:

    '''
    def __init__(self,doc,max_word_len=5,min_tf=0.000005,min_entropy=0.07,min_pmi=5):
        super(segdocument,self).__init__()
        self.max_word_len = max_word_len
        self.min_tf = min_tf
        self.min_entropy = min_entropy
        self.min_pmi = min_pmi
        #analysis documents
        self.word_info = self.gen_words(doc)
        filter_function = lambda f:len(f.text) > 1 and f.pmi > self.min_pmi and f.freq > self.min_tf\
                                   and min(f.left,f.right) > self.min_entropy
        self.word_tf_pmi_ent = map(lambda w :(w.text,len(w.text),w.freq,w.pmi,min(w.left,w.right)),filter(filter_function,self.word_info))

    def gen_words(self,doc):
        pattern = re.compile('[：“。”，！？、《》……；’‘ \n——\r\t]'.decode('utf-8'))
        doc = pattern.sub(r'',doc)
        word_index = extract_cadicateword(doc,self.max_word_len)
        word_cad = {} #后选词的字典
        for suffix in word_index:
            word = doc[suffix[0]:suffix[1]]
            if word not in word_cad:
                word_cad[word] = wordinfo(word)
                # record frequency of word and left neighbors and right neighbors
            word_cad[word].update_data(doc[suffix[0]-1:suffix[0]],doc[suffix[1]:suffix[1]+1])
        length = len(doc)
            #computing frequency of candicate word and entropy of left/right neighbors
        for word in word_cad:
            word_cad[word].compute_indexes(length)
        #ranking by length of word
        values = sorted(word_cad.values(),key=lambda x:len(x.text))
        for v in values:
            if len(v.text) == 1:
                continue
            v.compute_pmi(word_cad)
        # ranking by freq
        return sorted(values,key = lambda v: len(v.text),reverse = False)


if __name__ == '__main__':
        starttime = time.clock()
        path = os.path.abspath('.')
        decode_list = ['gb18030','gbk','utf-8','ISO-8859-2'] #providing multiple decode ways
        for decode_way in decode_list:
            try:
                doc = open(path+'/xiyouji.txt','r').read().decode(decode_way)
                print 'Great!{0} success to decode the document!!!'.format(decode_way)
                break
            except:
                print 'Oops!{0} cannot decode the document!'.format(decode_way)
        word = segdocument(doc)
        wordlist = []
        print 'result'
        for i in word.word_tf_pmi_ent:
            wordlist.append([i[0].encode('utf-8'),i[1],i[2],i[3]])
        seg = pd.DataFrame(wordlist,columns=['word','length','pmi','entropy'])
        seg.to_csv(path+'/extractword.csv',index=False)
        endtime = time.clock()
        print endtime-starttime
        






