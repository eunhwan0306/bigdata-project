6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ pwd
/c/Users/6-112/Desktop/빅데이터분석프로그래밍/bigdata-project-b- 주은환
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ ls
aaa.py  app.py  requirements.txt  venv/
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cd ..
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍
$ cd bitdata-project-b-주은환
bash: cd: bitdata-project-b-주은환: No such file or directory
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍
$ cd bigdata-project-b-주은환
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mkdir hello.md
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mkdir hello
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cat venv
cat: venv: Is a directory
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cat Lib
cat: Lib: No such file or directory
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cat app.py
import streamlit as st
import pandas as pd
# 페이지 설정
st.set_page_config(page_title="빅데이터 분석 프로젝트", page_icon="📊")
# 제목
st.title("빅데이터 분석 프로젝트")
st.write("첫 번째 Streamlit 앱입니다!")
# 구분선
st.divider()
# 간단한 데이터프레임 표시
st.subheader("샘플 데이터")
data = {
 "이름": ["김철수", "이영희", "박민수", "정수진", "최지훈"],     
 "학년": [3, 3, 3, 3, 3],
 "전공": ["AI소프트웨어", "AI소프트웨어", "AI소프트웨어", "AI소프트웨어", "AI소프트웨어"],
 "Python점수": [85, 92, 78, 95, 88]
}
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)
# 간단한 차트
st.subheader("Python 점수 차트")
st.bar_chart(df.set_index("이름")["Python점수"])
# 사이드바
st.sidebar.header("설정")
st.sidebar.write("이 영역은 사이드바입니다.")
name = st.sidebar.text_input("이름을 입력하세요")
if name:
 st.sidebar.write(f"안녕하세요, {name}님!")(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py
cp: missing destination file operand after 'app.py'
Try 'cp --help' for more information.
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp --help
Usage: cp [OPTION]... [-T] SOURCE DEST
  or:  cp [OPTION]... SOURCE... DIRECTORY
  or:  cp [OPTION]... -t DIRECTORY SOURCE...
Copy SOURCE to DEST, or multiple SOURCE(s) to DIRECTORY.

Mandatory arguments to long options are mandatory for short options too.
  -a, --archive                same as -dR --preserve=all        
      --attributes-only        don't copy the file data, just the attributes
      --backup[=CONTROL]       make a backup of each existing destination file
  -b                           like --backup but does not accept an argument
      --copy-contents          copy contents of special files when recursive
  -d                           same as --no-dereference --preserve=links
  -f, --force                  if an existing destination file cannot be
                                 opened, remove it and try again (this option
                                 is ignored when the -n option is also used)
  -i, --interactive            prompt before overwrite (overrides a previous -n
                                  option)
  -H                           follow command-line symbolic links in SOURCE
  -l, --link                   hard link files instead of copying
  -L, --dereference            always follow symbolic links in SOURCE
  -n, --no-clobber             do not overwrite an existing file (overrides
                                 a previous -i option)
  -P, --no-dereference         never follow symbolic links in SOURCE
  -p                           same as --preserve=mode,ownership,timestamps
      --preserve[=ATTR_LIST]   preserve the specified attributes (default:
                                 mode,ownership,timestamps), if possible
                                 additional attributes: context, links, xattr,
                                 all
      --no-preserve=ATTR_LIST  don't preserve the specified attributes
      --parents                use full source file name under DIRECTORY
  -R, -r, --recursive          copy directories recursively      
      --reflink[=WHEN]         control clone/CoW copies. See below
      --remove-destination     remove each existing destination file before
                                 attempting to open it (contrast with --force)
      --sparse=WHEN            control creation of sparse files. See below
      --strip-trailing-slashes  remove any trailing slashes from each SOURCE
                                 argument
  -s, --symbolic-link          make symbolic links instead of copying
  -S, --suffix=SUFFIX          override the usual backup suffix  
  -t, --target-directory=DIRECTORY  copy all SOURCE arguments into DIRECTORY
  -T, --no-target-directory    treat DEST as a normal file       
  -u, --update                 copy only when the SOURCE file is newer
                                 than the destination file or when the
                                 destination file is missing     
  -v, --verbose                explain what is being done        
  -x, --one-file-system        stay on this file system
  -Z                           set SELinux security context of destination
                                 file to default type
      --context[=CTX]          like -Z, or if CTX is specified then set the
                                 SELinux or SMACK security context to CTX
      --help     display this help and exit
      --version  output version information and exit

By default, sparse SOURCE files are detected by a crude heuristic and the
corresponding DEST file is made sparse as well.  That is the behavior
selected by --sparse=auto.  Specify --sparse=always to create a sparse DEST
file whenever the SOURCE file contains a long enough sequence of zero bytes.
Use --sparse=never to inhibit creation of sparse files.

When --reflink[=always] is specified, perform a lightweight copy, where the
data blocks are copied only when modified.  If this is not possible the copy
fails, or if --reflink=auto is specified, fall back to a standard copy.
Use --reflink=never to ensure a standard copy is performed.      

The backup suffix is '~', unless set with --suffix or SIMPLE_BACKUP_SUFFIX.
The version control method may be selected via the --backup option or through
the VERSION_CONTROL environment variable.  Here are the values:  

  none, off       never make backups (even if --backup is given) 
  numbered, t     make numbered backups
  existing, nil   numbered if numbered backups exist, simple otherwise
  simple, never   always make simple backups

As a special case, cp makes a backup of SOURCE when the force and backup
options are given and SOURCE and DEST are the same name for an existing,
regular file.

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report any translation bugs to <https://translationproject.org/team/>
Full documentation <https://www.gnu.org/software/coreutils/cp>   
or available locally via: info '(coreutils) cp invocation'       
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mkdir 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py
cp: missing destination file operand after 'app.py'
Try 'cp --help' for more information.
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py 3주차 실습
cp: target '실습' is not a directory
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py
mv: missing destination file operand after 'app.py'
Try 'mv --help' for more information.
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv 3주차  app.py
mv: cannot overwrite non-directory 'app.py' with directory '3주차'
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py venv
mv: cannot stat 'app.py': No such file or directory
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py
mv: missing destination file operand after 'app.py'
Try 'mv --help' for more information.
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py app.py(1)
bash: syntax error near unexpected token `('
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py app.py1
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cp app.py 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py app(1).py
bash: syntax error near unexpected token `('
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ mv app.py app1.py
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ git add .
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ git commit -m "명령어 연습"
[main 65d0506] 명령어 연습
 2 files changed, 28 insertions(+)
 rename app.py => "3\354\243\274\354\260\250/app.py" (100%)      
 create mode 100644 app1.py
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ git push
Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
Delta compression using up to 16 threads
Compressing objects: 100% (2/2), done.
Writing objects: 100% (3/3), 333 bytes | 333.00 KiB/s, done.     
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)    
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/eunhwan0306/bigdata-project
   0a5215f..65d0506  main -> main
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cd 3주차
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차 (main)
$ cd source
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차/source (main)
$ cd..
bash: cd..: command not found
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차/source (main)
$ cd ..
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차 (main)
$ cd ..
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ pip install python-dotenv
Collecting python-dotenv
  Downloading python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Downloading python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Installing collected packages: python-dotenv
Successfully installed python-dotenv-1.2.2

[notice] A new release of pip is available: 25.0.1 -> 26.0.1     
[notice] To update, run: python.exe -m pip install --upgrade pip 
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ ls
3주차/  aaa.py  app1.py  requirements.txt  venv/
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환 (main)
$ cd 3주차/
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차 (main)
$ ㅣㄴ
bash: ㅣㄴ: command not found
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차 (main)
$ ls
app.py  source/
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차 (main)
$ cd source/
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차/source (main)
$ ls
env_test.py
(venv) 
6-112@112-19 MINGW64 ~/Desktop/빅데이터분석프로그래밍/bigdata-project-b-주은환/3주차/source (main)
$ python env_test.py 
365d50323b937c53cc33056af78278ad54a0beb75e73cb2fe613db5a54987b20
(venv) 