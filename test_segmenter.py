import sys
sys.path.insert(0, '.')
from app.etl.extractor.base import RawTransaction
from app.etl.transformer.segmenter import segment_transactions

def test_segmentation():
    # Simulate PDF output where multiple transactions were merged into one description
    # because they lacked date columns.
    
    # 1. NACH with amount, merged with subsequent UPI/CR and UPI/DR
    raw_desc = (
        "NACH MONTHLY CASH ASSISTA 8527459677860 "
        "UPI/CR/127536852728/C KAMATCHI/IBKL/**RAN60@OKHDFCBANK/UPI/ "
        "07-Aug-2026 "
        "UPI/DR/621979888177/SBIPMOPAD/SBIP/**70750@SBIPAY/ "
        "UPI/CR/658673283261/G CHANDRA/ "
        "UPI/DR/622072649129/FLIPKART/ "
        "UPI/CR/658665497859/G CHANDRA/"
    )
    
    txn1 = RawTransaction(
        date="2026-08-07",
        description=raw_desc,
        amount="1000.00",
        balance="1000.64"
    )
    
    segmented = segment_transactions([txn1])
    
    assert len(segmented) == 6, f"Expected 6 transactions, got {len(segmented)}"
    
    # Transaction 1: NACH
    assert "NACH MONTHLY CASH ASSISTA" in segmented[0].description
    assert "UPI/CR" not in segmented[0].description
    assert segmented[0].amount == "1000.00"
    assert segmented[0].balance == "1000.64"
    
    # Transaction 2: UPI/CR
    assert "UPI/CR/127536852728/C KAMATCHI" in segmented[1].description
    assert segmented[1].amount is None
    assert segmented[1].balance is None
    
    # Transaction 3: UPI/DR
    assert "UPI/DR/621979888177/SBIPMOPAD" in segmented[2].description
    
    # Transaction 4: UPI/CR
    assert "UPI/CR/658673283261/G CHANDRA" in segmented[3].description
    
    # Transaction 5: UPI/DR FLIPKART
    assert "UPI/DR/622072649129/FLIPKART" in segmented[4].description
    
    # Transaction 6: UPI/CR
    assert "UPI/CR/658665497859/G CHANDRA" in segmented[5].description

    print("ALL SEGMENTATION TESTS PASSED")

if __name__ == "__main__":
    test_segmentation()
