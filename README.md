## Testing
To run all tests
```shell
brownie test
```

To run only zap tests
```shell
brownie test tests/zaps
```

You can also run forked tests for any network specified in [data](contracts/testing/tricrypto/data)
```shell
brownie test tests/zaps/forked --deployed_data arbitrum --network arbitrum-fork
```
