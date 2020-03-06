#!/usr/bin/env bash
set -euo pipefail

for test_suite in api cli endtoend installer longrun rhai rhci sys virtwho; do
    cat >"docs/api/tests.foreman.${test_suite}.rst" <<EOF
:mod:\`tests.foreman.${test_suite}\`
$(printf %$(( 21 + ${#test_suite} ))s | tr ' ' =)

.. automodule:: tests.foreman.${test_suite}
EOF

    find "tests/foreman/${test_suite}" -type f -name "test_*.py" | sort | while read -r file_name; do
        module_name="${file_name%.py}"
        module_name="${module_name//\//.}"

        cat >>"docs/api/tests.foreman.${test_suite}.rst" <<EOF

:mod:\`${module_name}\`
$(printf %$(( 7 + ${#module_name} ))s | tr ' ' -)

.. automodule:: ${module_name}
EOF
    done
done
