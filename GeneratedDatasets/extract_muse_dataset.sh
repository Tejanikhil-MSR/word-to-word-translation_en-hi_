# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

dl_path='https://dl.fbaipublicfiles.com/arrival'

mkdir muse_crosslingual_en_hi

## Downloading en-{} or {}-en dictionaries
lg="hi"
for suffix in .txt .0-5000.txt .5000-6500.txt
do
  fname=en-$lg$suffix
  curl -Lo muse_crosslingual_en_hi/$fname $dl_path/dictionaries/$fname
  fname=$lg-en$suffix
  curl -Lo muse_crosslingual_en_hi/$fname $dl_path/dictionaries/$fname
done