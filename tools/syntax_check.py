import py_compile
import glob
import sys

errors = []
for f in glob.glob('**/*.py', recursive=True):
    # 排除 tests 目录和文档目录
    if 'tests' in f or 'tests参考项目' in f or 'md_files' in f or '说明文档' in f:
        continue
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        errors.append(f"{f}: {e}")

with open('syntax_errors.txt', 'w', encoding='utf-8') as f:
    if not errors:
        f.write('NO_ERRORS')
    else:
        f.write('\n'.join(errors))

print('Syntax check complete. Results in syntax_errors.txt')
