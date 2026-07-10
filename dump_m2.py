import os, shutil

cache = os.path.expandvars(r'%USERPROFILE%\.gradle\caches\modules-2\files-2.1')
repo = os.path.expandvars(r'%USERPROFILE%\.m2\repository')

# Also include scoop gradle cache
import os
scoop_cache = os.path.expanduser(r'~\scoop\apps\gradle\current\.gradle\caches\modules-2\files-2.1')
caches = [cache]
if os.path.isdir(scoop_cache):
    caches.append(scoop_cache)

processed = set()

for cache_root in caches:
    for group in os.listdir(cache_root):
        group_path = os.path.join(cache_root, group)
        if not os.path.isdir(group_path):
            continue

        for artifact in os.listdir(group_path):
            art_path = os.path.join(group_path, artifact)
            if not os.path.isdir(art_path):
                continue

            for version in os.listdir(art_path):
                ver_path = os.path.join(art_path, version)
                if not os.path.isdir(ver_path):
                    continue

                key = '%s:%s:%s' % (group, artifact, version)
                if key in processed:
                    continue
                processed.add(key)

                target = os.path.join(repo, group.replace('.', '/'), artifact, version)
                os.makedirs(target, exist_ok=True)

                for root, dirs, files in os.walk(ver_path):
                    jar_found = False
                    for f in files:
                        if f.endswith('.jar'):
                            _, ext = os.path.splitext(f)
                            dest = os.path.join(target, '%s-%s%s' % (artifact, version, ext))
                            if not os.path.exists(dest):
                                shutil.copy2(os.path.join(root, f), dest)
                            jar_found = True
                            break

                    pom = os.path.join(target, '%s-%s.pom' % (artifact, version))
                    if not os.path.exists(pom):
                        with open(pom, 'w') as fp:
                            fp.write('<project xmlns="http://maven.apache.org/POM/4.0.0">\n')
                            fp.write('  <modelVersion>4.0.0</modelVersion>\n')
                            fp.write('  <groupId>%s</groupId>\n' % group)
                            fp.write('  <artifactId>%s</artifactId>\n' % artifact)
                            fp.write('  <version>%s</version>\n' % version)
                            fp.write('</project>\n')

                    if jar_found:
                        break

print('Total artifacts: %d' % len(processed))
