import sys

try:
    from cselab.cli import main
    main()
except KeyboardInterrupt:
    sys.exit(130)
except Exception as e:
    print(f"cselab: {e}", file=sys.stderr)
    sys.exit(1)
