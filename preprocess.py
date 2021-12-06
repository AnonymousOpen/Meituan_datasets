#!/usr/bin/env python36
# -*- coding: utf-8 -*-
"""
Created on July, 2018

@author: Tangrizzly
"""

import argparse
import time
import csv
import pickle
import operator
import datetime
import os

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='Meituan', help='dataset name: diginetica/yoochoose/sample')
opt = parser.parse_args()
print(opt)

dataset = 'Meituan_sh.csv'   #  'Meituan_bj.csv'

print("-- Starting @ %ss" % datetime.datetime.now())

with open(dataset, "r") as f:
    reader = csv.DictReader(f, delimiter=',')
    sess_clicks = {}
    sess_date = {}
    ctr = 0
    curid = -1
    curdate = None
    for data in reader:
        sessid = data['sessionID']
        if curdate and not curid == sessid:
            date = ''
            date = curdate
            sess_date[curid] = date
        curid = sessid
        
        item = int(data['itemID'])
        curdate = ''
        
        curdate = int(float(data['timestamp']))
        L = int(data['locationID'])
        T = int(data['timeID'])

        if sessid in sess_clicks:
            sess_clicks[sessid] += [(item, L, T)]
        else:
            sess_clicks[sessid] = [(item, L, T)]
        ctr += 1
    date = ''
    date = curdate
    sess_date[curid] = date
print('ctr:', ctr)
print("-- Reading data @ %ss" % datetime.datetime.now())

# Filter out length 1 sessions
for s in list(sess_clicks):
    if len(sess_clicks[s]) == 1:
        del sess_clicks[s]
        del sess_date[s]

# Count number of times each item appears
iid_counts = {}
for s in sess_clicks:
    seq = sess_clicks[s]
    for (iid, l, t) in seq:
        if iid in iid_counts:
            iid_counts[iid] += 1
        else:
            iid_counts[iid] = 1

sorted_counts = sorted(iid_counts.items(), key=operator.itemgetter(1))

def judge(inp):
    iid, l, t = inp
    return iid_counts[iid] >= 5

length = len(sess_clicks)
for s in list(sess_clicks):
    curseq = sess_clicks[s]
    filseq = list(filter(judge, curseq))
    if len(filseq) < 2 or len(filseq) > 20: # set your session len
        del sess_clicks[s]
        del sess_date[s]
    else:
        sess_clicks[s] = filseq

# Split out test set based on dates
dates = list(sess_date.items())
maxdate = dates[0][1]
mindate = dates[0][1]

for _, date in dates:
    if maxdate < date:
        maxdate = date
    if mindate > date:
        mindate = date

# 1 days for test
splitdate = 0
# the number of seconds for a day：86400
print("mindate:", mindate)
print("maxdate:", maxdate)
splitdate = maxdate - 86400 * 0.5

print('Splitting date', splitdate)      # Yoochoose: ('Split date', 1411930799.0)
tra_sess = filter(lambda x: x[1] < splitdate, dates)
tes_sess = filter(lambda x: x[1] > splitdate, dates)

# Sort sessions by date
tra_sess = sorted(tra_sess, key=operator.itemgetter(1))     # [(session_id, timestamp), (), ]
tes_sess = sorted(tes_sess, key=operator.itemgetter(1))     # [(session_id, timestamp), (), ]
print(len(tra_sess))    # 186670    # 7966257
print(len(tes_sess))    # 15979     # 15324
print(tra_sess[:3])
print(tes_sess[:3])
print("-- Splitting train set and test set @ %ss" % datetime.datetime.now())

# Choosing item count >=5 gives approximately the same number of items as reported in paper
item_dict = {}
l_dict = {}
t_dict = {}

# Convert training sessions to sequences and renumber items to start from 1, set 0 as mask in session
# Convert training sessions to sequences and renumber scenes to start from 1, set 0 as mask in session
def obtian_tra():
    train_ids = []
    train_seqs = []
    train_dates = []
    item_ctr = 1
    l_ctr= 1
    t_ctr= 1
    for s, date in tra_sess:
        seq = sess_clicks[s]
        outseq = []
        for (i,l,t) in seq:
            if i in item_dict:
                item_map = item_dict[i]
            else:
                item_map = item_ctr
                item_dict[i] = item_ctr
                item_ctr += 1
            
            if l in l_dict:
                l_map = l_dict[l]
            else:
                l_map = l_ctr
                l_dict[l] = l_ctr
                l_ctr += 1

            if t in t_dict:
                t_map = t_dict[t]
            else:
                t_map = t_ctr
                t_dict[t] = t_ctr
                t_ctr += 1

            outseq += [(item_map, l_map, t_map)]
        if len(outseq) < 2:  # Doesn't occur
            continue
        train_ids += [s]
        train_dates += [date]
        train_seqs += [outseq]
    print('item_ctr')
    print(item_ctr)
    print('l_num, t_num:', l_ctr, t_ctr)
    return train_ids, train_dates, train_seqs


# Convert test sessions to sequences, ignoring items that do not appear in training set
def obtian_tes():
    test_ids = []
    test_seqs = []
    test_dates = []
    for s, date in tes_sess:
        seq = sess_clicks[s]
        outseq = []
        for (i, l, t) in seq:
            if i in item_dict and l in l_dict and t in t_dict:
                outseq += [(item_dict[i], l_dict[l], t_dict[t])]
        if len(outseq) < 2:
            continue
        test_ids += [s]
        test_dates += [date]
        test_seqs += [outseq]
    return test_ids, test_dates, test_seqs


tra_ids, tra_dates, tra_seqs = obtian_tra()
tes_ids, tes_dates, tes_seqs = obtian_tes()


def process_seqs(iseqs, idates):
    out_seqs = []
    out_dates = []
    labs = []
    ids = []
    for id, seq, date in zip(range(len(iseqs)), iseqs, idates):
        for i in range(1, len(seq)):
            tar, _, _ = seq[-i]
            labs += [tar]
            out_seqs += [seq[:-i]]
            out_dates += [date]
            ids += [id]
    return out_seqs, out_dates, labs, ids


tr_seqs, tr_dates, tr_labs, tr_ids = process_seqs(tra_seqs, tra_dates)
te_seqs, te_dates, te_labs, te_ids = process_seqs(tes_seqs, tes_dates)
tra = (tr_seqs, tr_labs)
tes = (te_seqs, te_labs)
print('train_test')
print(len(tr_seqs))
print(len(te_seqs))
print(tr_seqs[:3], tr_dates[:3], tr_labs[:3])
print(te_seqs[:3], te_dates[:3], te_labs[:3])
all = 0

for seq in tra_seqs:
    all += len(seq)
for seq in tes_seqs:
    all += len(seq)
print('avg length: ', all/(len(tra_seqs) + len(tes_seqs) * 1.0))
print(all)

item_count = {}
l_count = {}
t_count = {}
for seq in tra_seqs:
    for (i,l, t) in seq:
        if i in item_count:
            item_count[i] += 1
        else:
            item_count[i] = 1

        if l in l_count:
            l_count[l] += 1
        else:
            l_count[l] = 1

        if t in t_count:
            t_count[t] += 1
        else:
            t_count[t] = 1

print("item_num, loc_num, time_num:",len(item_count), len(l_count), len(t_count))

'''
# save
pickle.dump(tra, open('train.txt', 'wb'))
pickle.dump(tes, open('test.txt', 'wb'))
pickle.dump(tra_seqs, open('all_train_seq.txt', 'wb'))
'''
print('Done.')

"""
clicks: 2825732
item_ctr
37682
l_num, t_num: 14 97
train_test sessions:
1049421
95885
avg length:  6.383367254370174
"""
