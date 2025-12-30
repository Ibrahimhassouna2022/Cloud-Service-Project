import argparse
import json
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.regression import LinearRegression
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.clustering import KMeans
from pyspark.ml.fpm import FPGrowth
from utils import get_spark_session, read_data, save_results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--params", required=True)
    args = parser.parse_args()
    
    params = json.loads(args.params)
    algo = params.get("algorithm", "linear_regression")
    target_col = params.get("target_col")
    feature_cols = params.get("feature_cols")
    
    spark = get_spark_session(f"MLJob_{algo}")
    
    try:
        df = read_data(spark, args.input).dropna()
        
        result_data = {"algorithm": algo}

        if algo in ["linear_regression", "logistic_regression", "kmeans"]:
             # Feature Assembly
             if not feature_cols:
                 # Auto-select numeric columns if not specified
                 feature_cols = [c for c, t in df.dtypes if t.startswith(('int', 'double', 'float')) and c != target_col]
             
             assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
             data = assembler.transform(df)

        if algo == "linear_regression":
            lr = LinearRegression(featuresCol="features", labelCol=target_col)
            model = lr.fit(data)
            summary = model.summary
            result_data["rmse"] = summary.rootMeanSquaredError
            result_data["r2"] = summary.r2
            result_data["coefficients"] = str(model.coefficients)
            result_data["intercept"] = model.intercept

        elif algo == "logistic_regression":
            lr = LogisticRegression(featuresCol="features", labelCol=target_col)
            model = lr.fit(data)
            summary = model.summary
            result_data["accuracy"] = summary.accuracy
            result_data["areaUnderROC"] = summary.areaUnderROC

        elif algo == "kmeans":
            k = int(params.get("k", 3))
            kmeans = KMeans(k=k, seed=1)
            model = kmeans.fit(data)
            # Make predictions
            predictions = model.transform(data)
            # Calculate cost (WSSE) - 'computeCost' is deprecated in newer versions, using ClusteringEvaluator is better but sticking to simple metrics
            # For simplicity let's return cluster centers
            centers = model.clusterCenters()
            result_data["cluster_centers"] = [c.tolist() for c in centers]

        elif algo == "fpgrowth":
            # Market Basket Analysis
            # Expects a column of items (array)
            items_col = params.get("items_col", df.columns[0]) # Default first col
            minSupport = float(params.get("minSupport", 0.1))
            minConfidence = float(params.get("minConfidence", 0.1))
            
            fp = FPGrowth(itemsCol=items_col, minSupport=minSupport, minConfidence=minConfidence)
            model = fp.fit(df)
            
            # Top frequent items
            freq_items = model.freqItems.limit(10).collect()
            result_data["frequent_items"] = [row.asDict() for row in freq_items]
            
            # Association rules
            rules = model.associationRules.limit(10).collect()
            result_data["association_rules"] = [row.asDict() for row in rules]

        else:
            result_data["error"] = "Unknown algorithm"

        save_results(result_data, args.output)

    except Exception as e:
        save_results({"error": str(e)}, args.output)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
