import konfi


@konfi.template()
class UserInfo:
    name: str
    country: str


@konfi.template()
class AppConfig:
    name: str = "konfi"
    user: UserInfo


if __name__ == "__main__":
    konfi.set_sources(
        konfi.YAML("config.yml"),
        konfi.Env(prefix="app_"),
    )

    # the return type is usually inferred, but some editors *cough* PyCharm
    # can't deal with the function alias
    config: AppConfig = konfi.load(AppConfig)

    print(f"Hello {config.user.name} from {config.user.country}")
    print(f"Welcome to {config.name}!")
