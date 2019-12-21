EC_TESTS = ec.test_context ec.test_curve ec.test_group ec.test_key_agreement ec.test_mod ec.test_model \
ec.test_mult ec.test_naf ec.test_op ec.test_point ec.test_signature

SCA_TESTS = sca.test_align sca.test_combine sca.test_edit sca.test_filter sca.test_match sca.test_process \
sca.test_sampling sca.test_test sca.test_trace sca.test_traceset

TESTS = ${EC_TESTS} ${SCA_TESTS}

test:
	nose2 -s test -A !slow -C -v ${TESTS}

test-plots:
	env PYECSCA_TEST_PLOTS=1 nose2 -s test -A !slow -C -v ${TESTS}

test-all:
	nose2 -s test -C -v ${TESTS}

typecheck:
	mypy pyecsca --ignore-missing-imports

.PHONY: test test-plots test-all typecheck