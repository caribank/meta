import pathlib
import pandas as pd
from cldfbench import Dataset as BaseDataset


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "cariban_meta"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        from cldfbench import CLDFSpec

        return CLDFSpec(
            dir=self.cldf_dir, module="Generic", metadata_fname="metadata.json"
        )

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        pass

    def cmd_makecldf(self, args):
        from cldfbench.catalogs import pyglottolog, Glottolog

        glottolog = pyglottolog.Glottolog(Glottolog.from_config().repo.working_dir)

        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        args.writer.cldf.add_component("LanguageTable")
        args.writer.cldf.remove_columns("LanguageTable", "Macroarea", "ISO639P3code")
        args.writer.cldf.add_columns(
            "LanguageTable",
            {"name": "IPA", "datatype": "string"},
            {"name": "Alternative_Names", "datatype": "string", "separator": "; "},
            {"name": "Shorthand", "datatype": "string"},
            {"name": "Dialect_Of", "datatype": "string"},
            {"name": "Alive", "datatype": "boolean"},
            {"name": "Proto_Language", "datatype": "boolean"},
        )
        args.writer.cldf.add_foreign_key(
            "LanguageTable", "Dialect_Of", "LanguageTable", "ID"
        )
        lgs = pd.read_csv(
            "raw/cariban_language_list.csv", dtype={"lat": "float", "long": "float"}
        )
        bool_dict = {"y": True, "n": False}
        for i, row in lgs.iterrows():
            print(row["ID"])
            if not pd.isnull(row["Glottocode"]):
                l = glottolog.languoid(row["Glottocode"])
                if not l.longitude:
                    print(f"No glottocoords for {l}, using own")
                elif row["lat"] != l.latitude or row["long"] != l.longitude:
                    print(f"Coordinate mismatch for {l}, using glottocode")
                    print(row["lat"], l.latitude)
                    print(row["long"], l.longitude)
                    row["lat"] = l.latitude
                    row["long"] = l.longitude
                elif row["lat"] == l.latitude and row["long"] == l.longitude:
                    print(f"Matching coords for {l}")
                    pass
            row.rename({"lat": "Latitude", "long": "Longitude"}, inplace=True)
            lg_dic = {
                "ID": row["ID"],
                "Name": row["Orthographic"],
                "Shorthand": row["Shorthand"],
                "Alive": bool_dict[row["Alive"]],
                "Comment": row["Comment"],
                "Proto_Language": (row["ID"][0] == "P"),
            }
            if not pd.isnull(row["Alternative_Names"]):
                print(row["Alternative_Names"].split("; "))
                lg_dic["Alternative_Names"] = row["Alternative_Names"].split("; ")

            for opt_col in ["Dialect_Of", "Latitude", "Longitude", "Glottocode", "IPA"]:
                if not pd.isnull(row[opt_col]):
                    lg_dic[opt_col] = row[opt_col]

            args.writer.objects["LanguageTable"].append(lg_dic)
