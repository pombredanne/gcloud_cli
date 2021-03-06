# gcloud-compute-ssh

Patches to PuTTY for 'gcloud compute ssh' on Windows.

## overview

Patch Windows PuTTY so that after
- copy pscp.exe scp.exe
- copy plink.exe ssh.exe
- copy pkeygen.exe ssh-keygen.exe
scp, ssh and ssh-keygen, from the command line, behave more like the OpenSsh
counterparts. Some behaviors are not covered -- mainly just enough to support
internal gcloud usage patterns.

## details

Changes fall into a few categories:
- Change cmdgen.c to generate pkeygen.exe which acts like ssh-keygen from the
  command line. Most of the changes are in this file. Major changes:
  - use windows libraries to generate cryptographic random data
  - output refactored to a loop that can generate more than one file
  - id, id.pub and id.ppk all generated by default
- Change all identity file read acceses to first check for a .ppk variant, for
  example, ``-i id'' will first check for id.ppk. This preserves the *ssh* and
  *scp -i* usage pattern.
- Change the default TERM environment variable value passed to the server by
  plink to check the local TERM setting (instead of "xterm"). If TERM is not set
  then "dumb" is used. This gives the proper hint to remote .profiles to
  refrain from colorizing prompts and ls(1) output.
- Eliminate the low hanging fruit of the MSVC 32 and 64 bit warnings. Most of
  these involve mixed combinations of [unsigned] int, [unsigned] long, size_t,
  and ssize_t. Some only show up in 64 bit compiles. Other culprits are
  strcpy(), strcat(), and sprintf() into fixed size buffers - they are handled
  by a homebrew szprintf() that supports a clean sized buffer paradigm. *Much
  more work* is needed in this area. A lot of the (int) and (size_t) casts
  should be replaced by proper variable and function typing, but that would
  require a meticulous code walkthrough.

## coverage

Link types:
- And ftp://foo.com/bar[download this] there.
- And http://foo.com/bar[look at this] there.
- And link:local/foo/bar[jump here] there.
- And https://foo.com/bar[look at this] there.
- And mailto:bozo@big.top[mail bozo] there.

Corner cases:
- And link:foo/bar[check this [really!!]]catenated.
- This *path* */*.c is not *bold*.
- This *path* */_.c is not _italic_.

This tests _dangling *embellishments that should not bleed
into the next section.

## examples

This is an example ``command'' line:

  $ echo 'example command line'

## next section

This text should not be embellished.


## NOTES

A special note.
