## Testing
To run all tests
```shell
brownie test
```

To run only zap tests
```shell
brownie test tests/zaps
```

To specify zap(`3pool` or `tricrypto` metapool)
```shell
brownie test tests/zaps --zap_base 3pool
```

You can also run forked tests for any network specified in [tricrypto data](contracts/testing/tricrypto/data) or
[3pool data](contracts/testing/3pool/data)
```shell
brownie test tests/zaps/forked --deployed_data arbitrum --network arbitrum-fork
```
