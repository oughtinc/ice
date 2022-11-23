from uvicorn import main

params_by_name = {p.name: p for p in main.params}
params_by_name["app"].default = "ice.routes.app:app"
params_by_name["port"].default = 8935

if __name__ == "__main__":
    main()
