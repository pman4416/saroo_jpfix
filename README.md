# SAROO 日本語パッチ作成ツール

公式で配布されているファームウェア ssfirm.bin のフォントを東雲フォントに変更し、文字化けなどに対処したフォントデータを作成する手順をまとめています。

- 2024/05/15版(firm_v0.5)対応
- 2024/06/17版(firm_v0.6)確認
- 2024/12/24版(firm_v0.7)対応

## 説明

SAROO起動時にサターンで実行される ssfirm.bin は前半 128KB が実行バイナリで、その後ろには多言語対応(CJK)フォントデータが結合されています。

※この関係か、exFAT形式(ファイル名がUTF-16LE)のSDカードしか利用できないようです

最近のバージョンアップ(2024/03/18)でプロポーショナルフォントおよび多言語ファイル名に対応しており、ファイル名として日本語も利用できますが、公式のフォントに含まれるのは簡体字・繁体字のみのようで日本語もほとんどカバーされておらず日本語フォントもパチモン臭いです。

ラテン語(U+0000～U+00FF)フォントはTimesRomanを使用しており、バイナリに埋め込みで更新には再ビルドが必要ですが、それ以外のフォントは結合されたフォントデータを利用しているようなのでフリーで利用できる東雲フォント14からデータを起こしました。

ただ、東雲フォントはJISX0208定義でそのままUnicodeに変換すると変換マップの問題でいくつか文字化けしてしまうため、これを無理やり再定義しています。また半角カナ(U+FF00～)も一部再定義していますが、半角カタカナ以外はまだ不完全です。

BDFフォントの変換は公式リポジトリに含まれる tools/bdfont をそのままコンパイルしたものを利用し、BDFフォントからのデータ抽出は PYTHON (3.10) を利用しています。

### v0.7未満について

文字コードの変換処理が、v0.7で一部修正されているため `fontjis2ucs.py` を修正しています。
もし v0.7未満向けにフォントデータを作成する場合は `tag:firm-v0.6` を使用してください。

## 実行バイナリの抽出

ssfirm.bin からフォントデータを除外した ssfirm_main.bin を以下のようにして取り出します
(ssfirm.bin はあらかじめリネームしておきます)

```
$ dd if=ssfirm.bin.org of=ssfirm_main.bin count=256
```

## フォントファイルの変換

`shinonome-0.9.11p1.tar.bz2` を配布サイト([shinonome font family](http://openlab.ring.gr.jp/efont/shinonome/))で[入手(2004-09-15 0.9.11 released)](http://openlab.ring.gr.jp/efont/dist/shinonome/)し、展開しておきます。

また、公式ファームウェアのリポジトリ([tpunix/SAROO: SAROO is a SEGA Saturn HDloader](https://github.com/tpunix/SAROO))の `tools/bdfont` ディレクトリで `bdfont` をビルドして持ってきます。

```
$ cd SAROO/tools/bdfont
$ make
$ cp bdfont ~/work/saroo_jp/
$ cd ~/work/saroo_jp/

$ tar -xjf shinonome-0.9.11p1.tar.bz2
```

フォントは PYTHON のスクリプトで結合・コード変更したものをバイナリに変換します
```
$ ./fontjis2ucs.py -j shinonome-0.9.11/bdf/shnmk14.bdf -h shinonome-0.9.11/bdf/shnm7x14r.bdf shnmrk14_ucs.bdf
$ ./bdfont shnmrk14_ucs.bdf -c font_shnmk14.bin
```

## バイナリファイル結合

```
$ cat ssfirm_main.bin font_shnmk14.bin > ssfirm.bin
```

出来た `ssfirm.bin` を SAROO にセットするマイクロSDカードの `SAROO/ssfirm.bin` にコピーしてください。


## サポートスクリプト

* 対象とする ssfirm.bin を `mk_jp_ssfirm.sh` と同じディレクトリにコピー
* 同ディレクトリに変換した日本語フォントバイナリを配置(`font_shnmk14.bin`)
* `mk_jp_ssfirm.sh` を実行するとフォントを更新した `ssfirm.bin` が得られる
```
$ ls
font_shnmk14.bin mk_jp_ssfirm.sh ssfirm.bin
$ ./mk_jp_ssfirm.sh
$ ls 
font_shnmk14.bin mk_jp_ssfirm.sh ssfirm.bin ssfirm.bin.org
```

## 起動しない・なんか動作がおかしい

動作しているSAROO環境のSDカードのファームを更新したら「起動しない」「カバー画像が出ない」などの症状を確認しています。
どうも、ファイルの削除などでディレクトリエントリの構成が複雑に変化した際にファイルの存在を確認できない、という症状が発生していると推測されます。(もしくはWindows上からのファイル操作との相性かも知れません)

### 回避方法？

SAROO フォルダのディレクトリ情報を作り直すとうまくいくようです。一番簡単なのは 
1. SAROO フォルダのリネーム(SAROO_org)
2. SAROO フォルダを新たに作成
3. SAROO_org フォルダの下のファイル・フォルダをすべて SAROO フォルダに移動する(コピーでも可だがその分の空き容量が必要になることに注意)

起動しない・カバー画像が表示されないなどの動作不良は上記で解決したので、予想はそれほど外してないのでは…？

### CD-DAが鳴らない

動作するようになって一安心、と思ったらCD-DAが鳴らない…どうもスロットの接触不良で発生することがあるらしい

[No music (i.e.: CDDA tracks) in any game! · Issue #238 · tpunix/SAROO](https://github.com/tpunix/SAROO/issues/238)

こちらも、挿しなおし・起動しなおしだけで正しく動作したので、接触不良でCD-DAだけ鳴らない、という症状が発声することもあるらしい。
