import os, shutil

cache = os.path.expandvars(r'%USERPROFILE%\.gradle\caches\modules-2\files-2.1')
repo = os.path.expandvars(r'%USERPROFILE%\.m2\repository')

for gdir in os.listdir(cache):
    gpath = os.path.join(cache, gdir)
    if not os.path.isdir(gpath):
        continue
    if not gdir.startswith('com.android'):
        continue

    mvn_path = gdir.replace('.', '/')

    for aid in os.listdir(gpath):
        apath = os.path.join(gpath, aid)
        if not os.path.isdir(apath):
            continue

        for ver in os.listdir(apath):
            vpath = os.path.join(apath, ver)
            if not os.path.isdir(vpath):
                continue

            target = os.path.join(repo, mvn_path, aid, ver)
            os.makedirs(target, exist_ok=True)

            copied = False
            for root, dirs, files in os.walk(vpath):
                for f in files:
                    if f.endswith('.jar'):
                        _, ext = os.path.splitext(f)
                        dest = os.path.join(target, '%s-%s%s' % (aid, ver, ext))
                        if not os.path.exists(dest):
                            shutil.copy2(os.path.join(root, f), dest)
                        copied = True
                        break
                if copied:
                    break

            pom = os.path.join(target, '%s-%s.pom' % (aid, ver))
            if not os.path.exists(pom):
                lines = [
                    '<project xmlns="http://maven.apache.org/POM/4.0.0">',
                    '  <modelVersion>4.0.0</modelVersion>',
                    '  <groupId>%s</groupId>' % gdir,
                    '  <artifactId>%s</artifactId>' % aid,
                    '  <version>%s</version>' % ver,
                    '</project>',
                ]
                with open(pom, 'w') as fp:
                    fp.write('\n'.join(lines) + '\n')

            print("%s:%s:%s" % (gdir, aid, ver))
