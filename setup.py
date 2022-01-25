from setuptools import setup


setup(
    name='cldfbench_cariban_meta',
    py_modules=['cldfbench_cariban_meta'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'cariban_meta=cldfbench_cariban_meta:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
