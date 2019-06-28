import konfi


@konfi.template()
class Credentials:
    user: str
    password: str


@konfi.template()
class AppConfig:
    name: str = "konfi"
    creds: Credentials


if __name__ == "__main__":
    konfi.set_sources(
        konfi.YAML("config.yml"),
        konfi.Env(prefix="app_"),
    )

    # the return type is usually inferred, but some editors *cough* PyCharm
    # can't deal with the function alias
    config: AppConfig = konfi.load(AppConfig)

    print(f"Hello {config.creds.name} from {config.name}")
